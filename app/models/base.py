"""
Base Model with common functionality
Implements Template Method pattern for CRUD operations
"""
from abc import ABC, abstractmethod
from datetime import datetime
from bson import ObjectId
from flask import current_app
from app import mongo


class BaseModel(ABC):
    """
    Abstract base model implementing Template Method pattern.
    Provides common CRUD operations for all MongoDB collections.
    """
    
    @property
    @abstractmethod
    def collection_name(self) -> str:
        """Return the MongoDB collection name."""
        pass
    
    @property
    def collection(self):
        """
        Get the MongoDB collection with connection validation.
        Raises RuntimeError if database is not connected.
        """
        db = self._get_db()
        if db is None:
            raise RuntimeError(
                f"MongoDB database not connected. "
                f"Cannot access collection '{self.collection_name}'"
            )
        return db[self.collection_name]
    
    @staticmethod
    def _get_db():
        """
        Safely get MongoDB database, handling both startup and runtime contexts.
        Returns None if database is not available.
        """
        # Primary: Flask-PyMongo's db attribute
        if mongo.db is not None:
            return mongo.db
        
        # Fallback: Try from current app extensions
        try:
            if hasattr(current_app, 'extensions') and 'pymongo' in current_app.extensions:
                pymongo_ext = current_app.extensions['pymongo']
                if 'MONGO' in pymongo_ext:
                    return pymongo_ext['MONGO'][1]
        except RuntimeError:
            pass  # Outside app context
        
        return None
    
    def to_dict(self) -> dict:
        """Convert model to dictionary for MongoDB insertion."""
        data = {}
        for key, value in self.__dict__.items():
            if not key.startswith('_'):
                if isinstance(value, datetime):
                    data[key] = value
                elif isinstance(value, ObjectId):
                    data[key] = value
                else:
                    data[key] = value
        return data
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create model instance from MongoDB document."""
        if data is None:
            return None
        instance = cls.__new__(cls)
        for key, value in data.items():
            setattr(instance, key if key != '_id' else 'id', value)
        return instance
    
    def save(self) -> ObjectId:
        """Save model to MongoDB. Template method."""
        data = self.to_dict()
        data['created_at'] = datetime.utcnow()
        result = self.collection.insert_one(data)
        self.id = result.inserted_id
        return result.inserted_id
    
    @classmethod
    def find_by_id(cls, id: ObjectId):
        """Find document by ID."""
        instance = cls.__new__(cls)
        data = instance.collection.find_one({'_id': ObjectId(id)})
        return cls.from_dict(data)
    
    @classmethod
    def find_one(cls, query: dict):
        """Find single document matching query."""
        instance = cls.__new__(cls)
        data = instance.collection.find_one(query)
        return cls.from_dict(data)
    
    @classmethod
    def find_many(cls, query: dict, sort=None, limit=None):
        """Find multiple documents matching query."""
        instance = cls.__new__(cls)
        cursor = instance.collection.find(query)
        if sort:
            cursor = cursor.sort(sort)
        if limit:
            cursor = cursor.limit(limit)
        return [cls.from_dict(doc) for doc in cursor]
    
    @classmethod
    def count(cls, query: dict = None) -> int:
        """Count documents matching query."""
        instance = cls.__new__(cls)
        return instance.collection.count_documents(query or {})
