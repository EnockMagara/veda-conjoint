"""
Session Service - Manages chat sessions and user flow
Implements Facade pattern for session management
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from bson import ObjectId
from flask import current_app

from app.models.user import User
from app.models.chat_session import ChatSession, SessionStatus
from app.models.user_response import UserResponse


class SessionService:
    """
    Facade for session management operations.
    Coordinates user creation, session lifecycle, and progress tracking.
    """
    
    @staticmethod
    def generate_session_seed() -> str:
        """Generate a unique seed for session randomization."""
        return str(uuid.uuid4())
    
    @classmethod
    def start_session(cls, email: str = None, name: str = None, 
                      zip_code: str = None) -> Dict[str, Any]:
        """
        Start a new chat session.
        
        Args:
            email: User email (optional at start)
            name: User name (optional at start)
            zip_code: User zip code (optional at start)
        
        Returns:
            Dictionary with session info and first question
        """
        user = None
        user_id = None
        
        # If we have user info, create or get user
        if email:
            user, created = User.create_or_get(email=email, name=name, zip_code=zip_code)
            user_id = user.id
        
        # Generate session seed for reproducible randomization
        session_seed = cls.generate_session_seed()
        
        # Create new session
        session = ChatSession(user_id=user_id, session_seed=session_seed)
        session.save()
        
        # Get first question
        questions = current_app.config['CHAT_QUESTIONS']
        first_question = questions[0]
        
        return {
            'session_id': str(session.id),
            'session_seed': session_seed,
            'status': session.status,
            'current_step': session.current_step,
            'question': first_question,
            'total_conjoint_rounds': current_app.config['CONJOINT_ROUNDS']
        }
    
    @classmethod
    def get_session(cls, session_id: str) -> Optional[ChatSession]:
        """Get session by ID."""
        return ChatSession.find_by_id(ObjectId(session_id))
    
    @classmethod
    def get_session_state(cls, session_id: str) -> Dict[str, Any]:
        """
        Get complete session state including user info and responses.
        """
        session = cls.get_session(session_id)
        if not session:
            return None
        
        # Get user info if linked
        user = None
        if session.user_id:
            user = User.find_by_id(session.user_id)
        
        # Get all responses
        responses = UserResponse.find_by_session(session.id)
        response_map = {r.question_id: r.normalized_value for r in responses}
        
        return {
            'session': session.to_json(),
            'user': user.to_json() if user else None,
            'responses': response_map,
            'total_conjoint_rounds': current_app.config['CONJOINT_ROUNDS']
        }
    
    @classmethod
    def link_user_to_session(cls, session_id: str, email: str, 
                             name: str = None, zip_code: str = None) -> User:
        """
        Link or create user and associate with session.
        """
        session = cls.get_session(session_id)
        if not session:
            raise ValueError("Session not found")
        
        user, created = User.create_or_get(email=email, name=name, zip_code=zip_code)
        
        # Update user info if provided
        if name and user.name != name:
            user.collection.update_one(
                {'_id': user.id},
                {'$set': {'name': name}}
            )
            user.name = name
        
        if zip_code and user.zip_code != zip_code:
            user.collection.update_one(
                {'_id': user.id},
                {'$set': {'zip_code': zip_code}}
            )
            user.zip_code = zip_code
        
        # Link to session
        if session.user_id != user.id:
            session.collection.update_one(
                {'_id': session.id},
                {'$set': {'user_id': user.id}}
            )
            session.user_id = user.id
        
        return user
    
    @classmethod
    def get_current_question(cls, session_id: str) -> Dict[str, Any]:
        """
        Get the current question for a session.
        """
        session = cls.get_session(session_id)
        if not session:
            return None
        
        questions = current_app.config['CHAT_QUESTIONS']
        
        # Find current question
        for question in questions:
            if question['id'] == session.current_step:
                return cls._format_question(session, question)
        
        return None
    
    @classmethod
    def advance_to_next_step(cls, session_id: str) -> Dict[str, Any]:
        """
        Advance session to the next question/step.
        """
        session = cls.get_session(session_id)
        if not session:
            return None
        
        questions = current_app.config['CHAT_QUESTIONS']
        question_ids = [q['id'] for q in questions]
        
        current_idx = question_ids.index(session.current_step)
        
        # Check if we're in conjoint mode and NOT complete
        if session.current_step == 'conjoint':
            total_rounds = current_app.config['CONJOINT_ROUNDS']
            # Only stay in conjoint if we haven't completed all rounds
            if session.current_round < total_rounds:
                # Continue conjoint rounds
                session.update_progress('conjoint', session.current_round + 1)
                return cls.get_current_question(session_id)
            # If current_round >= total_rounds, fall through to move to next step
        
        # Move to next question
        if current_idx < len(questions) - 1:
            next_question = questions[current_idx + 1]
            # Reset round to 1 only if entering conjoint, otherwise keep 0
            new_round = 1 if next_question['id'] == 'conjoint' else 0
            session.update_progress(next_question['id'], new_round)
            return cls._format_question(session, next_question)
        else:
            # Session complete
            session.complete()
            return {
                'complete': True,
                'message': 'Session completed successfully'
            }
    
    @classmethod
    def _format_question(cls, session: ChatSession, question: Dict) -> Dict[str, Any]:
        """Format question with user data interpolation."""
        result = question.copy()
        
        # Get branding data
        branding_data = {
            'assistant_name': current_app.config.get('ASSISTANT_NAME', 'Jill'),
            'company_name': current_app.config.get('COMPANY_NAME', 'Veda-')
        }
        
        # Get user data for interpolation
        user_data = {}
        if session.user_id:
            user = User.find_by_id(session.user_id)
            if user:
                user_data['name'] = user.name or 'there'
        
        # Get responses for interpolation
        responses = UserResponse.find_by_session(session.id)
        for r in responses:
            user_data[r.question_id] = r.normalized_value
        
        # Merge all interpolation data
        interpolation_data = {**branding_data, **user_data}
        
        # Interpolate message
        try:
            result['message'] = question['message'].format(**interpolation_data)
        except KeyError:
            pass  # Keep original message if interpolation fails
        
        # Add session context
        result['session_id'] = str(session.id)
        result['current_round'] = session.current_round
        result['total_rounds'] = current_app.config['CONJOINT_ROUNDS']
        
        return result
    
    @classmethod
    def complete_session(cls, session_id: str):
        """Mark session as completed."""
        session = cls.get_session(session_id)
        if session:
            session.complete()
    
    @classmethod
    def abandon_session(cls, session_id: str):
        """Mark session as abandoned."""
        session = cls.get_session(session_id)
        if session:
            session.abandon()
