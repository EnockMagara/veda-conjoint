"""
User Model - Stores minimal participant information
PII is separated from experimental data
"""
from datetime import datetime
from bson import ObjectId
from app.models.base import BaseModel


class User(BaseModel):
    """
    User model for participant information.
    
    Fields:
        - email (string, indexed, unique)
        - name (string)
        - zip_code (string)
        - timezone (string)
        - created_at (date)
    """
    
    collection_name = 'users'
    
    def __init__(self, email: str, name: str = None, zip_code: str = None, 
                 timezone: str = None):
        self.email = email
        self.name = name
        self.zip_code = zip_code
        self.timezone = timezone
        self.created_at = datetime.utcnow()
        self.id = None
    
    @classmethod
    def find_by_email(cls, email: str):
        """Find user by email address."""
        return cls.find_one({'email': email})
    
    @classmethod
    def create_or_get(cls, email: str, name: str = None, zip_code: str = None):
        """
        Get existing user or create new one.
        Ensures email uniqueness.
        """
        existing = cls.find_by_email(email)
        if existing:
            return existing, False
        
        user = cls(email=email, name=name, zip_code=zip_code)
        user.save()
        return user, True
    
    @classmethod
    def ensure_indexes(cls):
        """Create indexes for the collection."""
        instance = cls.__new__(cls)
        instance.collection.create_index('email', unique=True)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'email': self.email,
            'name': self.name,
            'zip_code': self.zip_code,
            'timezone': self.timezone,
            'created_at': self.created_at
        }
    
    def to_json(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        return {
            'id': str(self.id) if self.id else None,
            'email': self.email,
            'name': self.name,
            'zip_code': self.zip_code,
            'timezone': self.timezone,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
