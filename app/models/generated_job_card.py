"""
GeneratedJobCard Model - Stores generated schematic job ads shown to users
"""
from datetime import datetime
from enum import Enum
from bson import ObjectId
from app.models.base import BaseModel


class CardLabel(Enum):
    """Card label enumeration."""
    A = 'A'
    B = 'B'


class GeneratedJobCard(BaseModel):
    """
    GeneratedJobCard model for storing job cards shown in conjoint.
    
    Fields:
        - session_id (ObjectId, indexed)
        - card_label (enum: A | B)
        - attributes (object: attribute_key → level_id)
        - rendered_text (string)
        - round_number (number)
    
    Note: Stored to ensure exact exposure tracking
          Generated using session_seed for reproducibility
    """
    
    collection_name = 'generated_job_cards'
    
    def __init__(self, session_id: ObjectId, card_label: str, 
                 attributes: dict, rendered_text: str, round_number: int):
        self.session_id = session_id
        self.card_label = card_label
        self.attributes = attributes  # {attribute_key: level_id, ...}
        self.rendered_text = rendered_text
        self.round_number = round_number
        self.created_at = datetime.utcnow()
        self.id = None
    
    @classmethod
    def find_by_session(cls, session_id: ObjectId):
        """Find all job cards for a session."""
        return cls.find_many(
            {'session_id': ObjectId(session_id)},
            sort=[('round_number', 1), ('card_label', 1)]
        )
    
    @classmethod
    def find_by_round(cls, session_id: ObjectId, round_number: int):
        """Find job cards for a specific round."""
        return cls.find_many({
            'session_id': ObjectId(session_id),
            'round_number': round_number
        })
    
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
            'card_label': self.card_label,
            'attributes': self.attributes,
            'rendered_text': self.rendered_text,
            'round_number': self.round_number,
            'created_at': self.created_at
        }
    
    def to_json(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        return {
            'id': str(self.id) if self.id else None,
            'session_id': str(self.session_id) if self.session_id else None,
            'card_label': self.card_label,
            'attributes': self.attributes,
            'rendered_text': self.rendered_text,
            'round_number': self.round_number,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
