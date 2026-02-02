"""
Response Service - Handles user response collection and processing
"""
from typing import Dict, Any, Optional
from bson import ObjectId

from app.models.user_response import UserResponse
from app.models.chat_session import ChatSession


class ResponseService:
    """
    Service for managing user responses to chat questions.
    Handles response storage and normalization.
    """
    
    @classmethod
    def save_response(cls, session_id: str, question_id: str,
                      question_type: str, raw_input: str,
                      normalized_value: Any = None) -> UserResponse:
        """
        Save a user response (immutable after save).
        
        Args:
            session_id: Session ObjectId string
            question_id: Question identifier
            question_type: Type of question (text, choice, number)
            raw_input: Raw user input
            normalized_value: Optional normalized/processed value
        
        Returns:
            Saved UserResponse object
        """
        # Check for existing response
        existing = UserResponse.get_response(ObjectId(session_id), question_id)
        if existing:
            # Responses are immutable - return existing
            return existing
        
        # Create new response
        response = UserResponse(
            session_id=ObjectId(session_id),
            question_id=question_id,
            question_type=question_type,
            raw_input=raw_input,
            normalized_value=normalized_value or raw_input
        )
        response.save()
        
        return response
    
    @classmethod
    def get_response(cls, session_id: str, question_id: str) -> Optional[UserResponse]:
        """Get a specific response."""
        return UserResponse.get_response(ObjectId(session_id), question_id)
    
    @classmethod
    def get_all_responses(cls, session_id: str) -> Dict[str, Any]:
        """Get all responses for a session as a dictionary."""
        responses = UserResponse.find_by_session(ObjectId(session_id))
        return {r.question_id: {
            'raw_input': r.raw_input,
            'normalized_value': r.normalized_value,
            'question_type': r.question_type,
            'timestamp': r.timestamp.isoformat() if r.timestamp else None
        } for r in responses}
    
    @classmethod
    def normalize_text_response(cls, raw_input: str, question_id: str) -> str:
        """
        Normalize text responses.
        Can be extended with LLM processing in future.
        """
        # Basic normalization
        normalized = raw_input.strip()
        
        # Question-specific normalization
        if question_id == 'email':
            normalized = normalized.lower()
        elif question_id == 'zip_code':
            # Extract numeric portion
            normalized = ''.join(c for c in normalized if c.isdigit())[:5]
        elif question_id == 'name':
            # Title case for names
            normalized = normalized.title()
        
        return normalized
    
    @classmethod
    def validate_response(cls, question_id: str, raw_input: str) -> Dict[str, Any]:
        """
        Validate a response before saving.
        
        Returns:
            Dictionary with 'valid' boolean and 'error' message if invalid
        """
        if not raw_input or not raw_input.strip():
            return {'valid': False, 'error': 'Response cannot be empty'}
        
        # Question-specific validation
        if question_id == 'email':
            if '@' not in raw_input or '.' not in raw_input:
                return {'valid': False, 'error': 'Please enter a valid email address'}
        
        elif question_id == 'zip_code':
            digits = ''.join(c for c in raw_input if c.isdigit())
            if len(digits) < 5:
                return {'valid': False, 'error': 'Please enter a valid zip code'}
        
        elif question_id == 'name':
            if len(raw_input.strip()) < 2:
                return {'valid': False, 'error': 'Please enter your name'}
        
        return {'valid': True}
