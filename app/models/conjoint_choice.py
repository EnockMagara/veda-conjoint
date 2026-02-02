"""
ConjointChoice Model - Records user choices between A/B job cards
Core dataset for analysis - No updates allowed
"""
from datetime import datetime
from bson import ObjectId
from app.models.base import BaseModel


class ConjointChoice(BaseModel):
    """
    ConjointChoice model for recording user A/B selections.
    
    Fields:
        - session_id (ObjectId, indexed)
        - round_number (number)
        - choice (enum: A | B)
        - response_time_ms (number)
        - timestamp (date)
    
    Note: Core dataset for conjoint analysis
          No updates allowed - immutable
    """
    
    collection_name = 'conjoint_choices'
    
    def __init__(self, session_id: ObjectId, round_number: int,
                 choice: str, response_time_ms: int):
        self.session_id = session_id
        self.round_number = round_number
        self.choice = choice  # 'A' or 'B'
        self.response_time_ms = response_time_ms
        self.timestamp = datetime.utcnow()
        self.id = None
    
    @classmethod
    def find_by_session(cls, session_id: ObjectId):
        """Find all choices for a session."""
        return cls.find_many(
            {'session_id': ObjectId(session_id)},
            sort=[('round_number', 1)]
        )
    
    @classmethod
    def get_choice(cls, session_id: ObjectId, round_number: int):
        """Get choice for a specific round."""
        return cls.find_one({
            'session_id': ObjectId(session_id),
            'round_number': round_number
        })
    
    @classmethod
    def get_all_choices_with_cards(cls, session_id: ObjectId):
        """
        Get all choices with their associated job cards.
        Useful for analysis export.
        """
        from app.models.generated_job_card import GeneratedJobCard
        
        choices = cls.find_by_session(session_id)
        result = []
        
        for choice in choices:
            cards = GeneratedJobCard.find_by_round(session_id, choice.round_number)
            card_a = next((c for c in cards if c.card_label == 'A'), None)
            card_b = next((c for c in cards if c.card_label == 'B'), None)
            
            result.append({
                'round_number': choice.round_number,
                'choice': choice.choice,
                'response_time_ms': choice.response_time_ms,
                'card_a_attributes': card_a.attributes if card_a else None,
                'card_b_attributes': card_b.attributes if card_b else None,
                'timestamp': choice.timestamp
            })
        
        return result
    
    @classmethod
    def ensure_indexes(cls):
        """Create indexes for the collection."""
        instance = cls.__new__(cls)
        instance.collection.create_index('session_id')
        instance.collection.create_index([('session_id', 1), ('round_number', 1)])
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'session_id': self.session_id,
            'round_number': self.round_number,
            'choice': self.choice,
            'response_time_ms': self.response_time_ms,
            'timestamp': self.timestamp
        }
    
    def to_json(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        return {
            'id': str(self.id) if self.id else None,
            'session_id': str(self.session_id) if self.session_id else None,
            'round_number': self.round_number,
            'choice': self.choice,
            'response_time_ms': self.response_time_ms,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
