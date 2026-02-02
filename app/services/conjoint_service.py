"""
Conjoint Service - Manages conjoint experiment logic
Implements Strategy pattern coordination for job card generation
"""
from typing import Dict, Any, List, Optional, Tuple
from bson import ObjectId
from flask import current_app

from app.models.chat_session import ChatSession
from app.models.generated_job_card import GeneratedJobCard
from app.models.conjoint_choice import ConjointChoice
from app.models.job_attribute import JobAttribute
from app.services.attribute_service import AttributeService
from app.patterns.factory import JobCardFactory
from app.patterns.strategy import (
    SeededRandomStrategy,
    BalancedRandomStrategy,
    FullFactorialStrategy
)


class ConjointService:
    """
    Service for managing conjoint experiment operations.
    Coordinates card generation, display, and choice recording.
    """
    
    # Strategy registry for different randomization approaches
    STRATEGIES = {
        'seeded': SeededRandomStrategy,
        'balanced': BalancedRandomStrategy,
        'factorial': FullFactorialStrategy
    }
    
    def __init__(self, strategy_name: str = 'balanced'):
        """
        Initialize conjoint service with specified strategy.
        
        Args:
            strategy_name: Name of randomization strategy
        """
        strategy_class = self.STRATEGIES.get(strategy_name, BalancedRandomStrategy)
        self.strategy = strategy_class()
        self.factory = JobCardFactory(self.strategy)
    
    @classmethod
    def get_round_cards(cls, session_id: str, round_number: int) -> Dict[str, Any]:
        """
        Get or generate job cards for a specific round.
        
        Args:
            session_id: Session ObjectId string
            round_number: Round number (1-indexed)
        
        Returns:
            Dictionary with card_a and card_b data
        """
        session = ChatSession.find_by_id(ObjectId(session_id))
        if not session:
            return None
        
        # Check for existing cards
        existing_cards = GeneratedJobCard.find_by_round(
            ObjectId(session_id), round_number
        )
        
        if len(existing_cards) == 2:
            # Return existing cards
            card_a = next((c for c in existing_cards if c.card_label == 'A'), None)
            card_b = next((c for c in existing_cards if c.card_label == 'B'), None)
        else:
            # Generate new cards
            service = cls()
            card_a, card_b = service.factory.create_and_save_card_pair(
                ObjectId(session_id),
                round_number,
                session.session_seed
            )
        
        # Get attribute definitions for display (via AttributeService for initialization safety)
        attributes = AttributeService.get_all_attributes()
        attr_map = {a.attribute_key: a for a in attributes}
        
        return {
            'round_number': round_number,
            'total_rounds': current_app.config['CONJOINT_ROUNDS'],
            'card_a': cls._format_card(card_a, attr_map),
            'card_b': cls._format_card(card_b, attr_map)
        }
    
    @classmethod
    def _format_card(cls, card: GeneratedJobCard, 
                     attr_map: Dict[str, JobAttribute]) -> Dict[str, Any]:
        """Format job card for frontend display."""
        attributes = []
        
        for attr_key, level_id in card.attributes.items():
            attr_def = attr_map.get(attr_key)
            if attr_def:
                attributes.append({
                    'key': attr_key,
                    'label': attr_def.display_name,
                    'value': attr_def.get_level_text(level_id),
                    'level_id': level_id
                })
        
        return {
            'id': str(card.id),
            'label': card.card_label,
            'attributes': attributes,
            'rendered_text': card.rendered_text
        }
    
    @classmethod
    def record_choice(cls, session_id: str, round_number: int,
                      choice: str, response_time_ms: int) -> Dict[str, Any]:
        """
        Record user's A/B choice for a round.
        
        Args:
            session_id: Session ObjectId string
            round_number: Round number
            choice: 'A' or 'B'
            response_time_ms: Time taken to make choice
        
        Returns:
            Confirmation and next round info
        """
        # Validate choice
        if choice not in ('A', 'B'):
            raise ValueError("Choice must be 'A' or 'B'")
        
        # Check if choice already recorded
        existing = ConjointChoice.get_choice(ObjectId(session_id), round_number)
        if existing:
            return {
                'error': 'Choice already recorded for this round',
                'existing_choice': existing.choice
            }
        
        # Record choice (immutable)
        conjoint_choice = ConjointChoice(
            session_id=ObjectId(session_id),
            round_number=round_number,
            choice=choice,
            response_time_ms=response_time_ms
        )
        conjoint_choice.save()
        
        # Update session round progress
        session = ChatSession.find_by_id(ObjectId(session_id))
        total_rounds = current_app.config['CONJOINT_ROUNDS']
        
        # Always update session's current_round to track progress
        session.update_progress('conjoint', round_number)
        
        if round_number >= total_rounds:
            # Conjoint complete - advance session to next step (completion)
            # This moves the session past 'conjoint' to 'completion'
            return {
                'success': True,
                'choice_id': str(conjoint_choice.id),
                'conjoint_complete': True,
                'round_number': round_number
            }
        else:
            return {
                'success': True,
                'choice_id': str(conjoint_choice.id),
                'conjoint_complete': False,
                'next_round': round_number + 1
            }
    
    @classmethod
    def get_session_results(cls, session_id: str) -> Dict[str, Any]:
        """
        Get all conjoint results for a session.
        Useful for analysis and export.
        """
        session = ChatSession.find_by_id(ObjectId(session_id))
        if not session:
            return None
        
        choices = ConjointChoice.get_all_choices_with_cards(ObjectId(session_id))
        
        return {
            'session_id': session_id,
            'session_seed': session.session_seed,
            'status': session.status,
            'total_rounds': len(choices),
            'choices': choices
        }
    
    @classmethod
    def get_analysis_data(cls, session_ids: List[str] = None) -> List[Dict]:
        """
        Get data formatted for conjoint analysis.
        Returns flattened records suitable for logit/probit models.
        """
        from app import mongo
        
        # Build query
        query = {}
        if session_ids:
            query['session_id'] = {'$in': [ObjectId(sid) for sid in session_ids]}
        
        # Get all choices
        choices = list(mongo.db.conjoint_choices.find(query))
        
        analysis_data = []
        
        for choice in choices:
            session_id = choice['session_id']
            round_num = choice['round_number']
            
            # Get corresponding cards
            cards = list(mongo.db.generated_job_cards.find({
                'session_id': session_id,
                'round_number': round_num
            }))
            
            card_a = next((c for c in cards if c['card_label'] == 'A'), None)
            card_b = next((c for c in cards if c['card_label'] == 'B'), None)
            
            if card_a and card_b:
                # Create analysis record
                record = {
                    'session_id': str(session_id),
                    'round_number': round_num,
                    'choice': choice['choice'],
                    'chose_a': 1 if choice['choice'] == 'A' else 0,
                    'response_time_ms': choice['response_time_ms'],
                    'timestamp': choice['timestamp'].isoformat()
                }
                
                # Add card A attributes
                for key, value in card_a['attributes'].items():
                    record[f'a_{key}'] = value
                
                # Add card B attributes
                for key, value in card_b['attributes'].items():
                    record[f'b_{key}'] = value
                
                analysis_data.append(record)
        
        return analysis_data
