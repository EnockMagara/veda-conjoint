"""
UserResponse Model - Stores structured answers from chatbot questions
Immutable after write
"""
from datetime import datetime
from enum import Enum
from bson import ObjectId
from app.models.base import BaseModel


class QuestionType(Enum):
    """Question type enumeration."""
    TEXT = 'text'
    CHOICE = 'choice'
    NUMBER = 'number'
    INFO = 'info'


class UserResponse(BaseModel):
    """
    UserResponse model for storing chat question answers.
    
    Fields:
        - session_id (ObjectId, indexed)
        - question_id (string)
        - question_type (enum: text | choice | number)
        - normalized_value (string | number | array)
        - raw_input (string)
        - timestamp (date)
    
    Note: Immutable after write - no updates allowed
    """
    
    collection_name = 'user_responses'
    
    def __init__(self, session_id: ObjectId, question_id: str, 
                 question_type: str, raw_input: str, 
                 normalized_value=None):
        self.session_id = session_id
        self.question_id = question_id
        self.question_type = question_type
        self.raw_input = raw_input
        self.normalized_value = normalized_value or raw_input
        self.timestamp = datetime.utcnow()
        self.id = None
    
    @classmethod
    def find_by_session(cls, session_id: ObjectId):
        """Find all responses for a session."""
        return cls.find_many(
            {'session_id': ObjectId(session_id)},
            sort=[('timestamp', 1)]
        )
    
    @classmethod
    def get_response(cls, session_id: ObjectId, question_id: str):
        """Get specific response for a question in a session."""
        return cls.find_one({
            'session_id': ObjectId(session_id),
            'question_id': question_id
        })
    
    @classmethod
    def ensure_indexes(cls):
        """Create indexes for the collection."""
        instance = cls.__new__(cls)
        instance.collection.create_index('session_id')
        instance.collection.create_index([('session_id', 1), ('question_id', 1)])
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'session_id': self.session_id,
            'question_id': self.question_id,
            'question_type': self.question_type,
            'raw_input': self.raw_input,
            'normalized_value': self.normalized_value,
            'timestamp': self.timestamp
        }
    
    def to_json(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        return {
            'id': str(self.id) if self.id else None,
            'session_id': str(self.session_id) if self.session_id else None,
            'question_id': self.question_id,
            'question_type': self.question_type,
            'raw_input': self.raw_input,
            'normalized_value': self.normalized_value,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
