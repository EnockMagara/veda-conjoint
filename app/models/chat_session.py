"""
ChatSession Model - Represents a single chatbot/form interaction
"""
from datetime import datetime
from enum import Enum
from bson import ObjectId
from app.models.base import BaseModel


class SessionStatus(Enum):
    """Session status enumeration."""
    STARTED = 'started'
    COMPLETED = 'completed'
    ABANDONED = 'abandoned'


class ChatSession(BaseModel):
    """
    ChatSession model for tracking chatbot interactions.
    
    Fields:
        - user_id (ObjectId, indexed)
        - session_seed (string) - controls randomization for reproducibility
        - status (enum: started | completed | abandoned)
        - started_at (date)
        - completed_at (date)
        - current_step (string) - tracks progress in chat flow
        - current_round (number) - tracks conjoint round
    """
    
    collection_name = 'chat_sessions'
    
    def __init__(self, user_id: ObjectId = None, session_seed: str = None):
        self.user_id = user_id
        self.session_seed = session_seed
        self.status = SessionStatus.STARTED.value
        self.started_at = datetime.utcnow()
        self.completed_at = None
        self.current_step = 'welcome'
        self.current_round = 0
        self.id = None
    
    @classmethod
    def find_by_user(cls, user_id: ObjectId, status: str = None):
        """Find sessions by user ID."""
        query = {'user_id': ObjectId(user_id)}
        if status:
            query['status'] = status
        return cls.find_many(query, sort=[('started_at', -1)])
    
    @classmethod
    def get_active_session(cls, user_id: ObjectId):
        """Get user's active (started) session."""
        return cls.find_one({
            'user_id': ObjectId(user_id),
            'status': SessionStatus.STARTED.value
        })
    
    def complete(self):
        """Mark session as completed."""
        self.status = SessionStatus.COMPLETED.value
        self.completed_at = datetime.utcnow()
        self.collection.update_one(
            {'_id': self.id},
            {'$set': {
                'status': self.status,
                'completed_at': self.completed_at
            }}
        )
    
    def abandon(self):
        """Mark session as abandoned."""
        self.status = SessionStatus.ABANDONED.value
        self.collection.update_one(
            {'_id': self.id},
            {'$set': {'status': self.status}}
        )
    
    def update_progress(self, step: str, round_number: int = None):
        """Update session progress."""
        update = {'current_step': step}
        if round_number is not None:
            update['current_round'] = round_number
        
        self.current_step = step
        if round_number is not None:
            self.current_round = round_number
            
        self.collection.update_one(
            {'_id': self.id},
            {'$set': update}
        )
    
    @classmethod
    def ensure_indexes(cls):
        """Create indexes for the collection."""
        instance = cls.__new__(cls)
        instance.collection.create_index('user_id')
        instance.collection.create_index([('user_id', 1), ('status', 1)])
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'user_id': self.user_id,
            'session_seed': self.session_seed,
            'status': self.status,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'current_step': self.current_step,
            'current_round': self.current_round
        }
    
    def to_json(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        return {
            'id': str(self.id) if self.id else None,
            'user_id': str(self.user_id) if self.user_id else None,
            'session_seed': self.session_seed,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'current_step': self.current_step,
            'current_round': self.current_round
        }
