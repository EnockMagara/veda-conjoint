"""
Attribute Service - Manages job attributes for conjoint analysis
"""
from typing import List, Dict, Any, Optional
from flask import current_app
from app.models.job_attribute import JobAttribute, DEFAULT_JOB_ATTRIBUTES
from app import mongo


class AttributeService:
    """
    Service for managing conjoint job attributes.
    Implements Singleton pattern for attribute caching with lazy initialization.
    """
    
    _initialized = False
    _cached_attributes = None
    
    @classmethod
    def _get_db(cls):
        """
        Safely get MongoDB database connection.
        Works both during startup and runtime.
        """
        # Try Flask-PyMongo's db
        if mongo.db is not None:
            return mongo.db
        
        # Fallback: Try to get from current app context
        try:
            if hasattr(current_app, 'extensions') and 'pymongo' in current_app.extensions:
                return current_app.extensions['pymongo']['MONGO'][1]
        except RuntimeError:
            pass  # Outside app context
        
        return None
    
    @classmethod
    def initialize_default_attributes(cls) -> bool:
        """
        Initialize default job attributes if not already present.
        Uses defensive initialization with lazy loading pattern.
        
        Returns True if successful.
        """
        try:
            db = cls._get_db()
            if db is None:
                # Defer initialization - will be done on first access
                print("⏳ MongoDB not ready, deferring attribute initialization")
                return False
            
            # Check if attributes already exist
            existing_count = db.job_attributes.count_documents({})
            
            if existing_count == 0:
                # Seed default attributes
                for attr_data in DEFAULT_JOB_ATTRIBUTES:
                    db.job_attributes.insert_one({
                        'attribute_key': attr_data['attribute_key'],
                        'display_name': attr_data['display_name'],
                        'levels': attr_data['levels']
                    })
                print(f"✓ Initialized {len(DEFAULT_JOB_ATTRIBUTES)} default job attributes")
            else:
                print(f"✓ Found {existing_count} existing job attributes")
            
            cls._initialized = True
            cls._cached_attributes = None  # Clear cache to reload
            return True
            
        except Exception as e:
            print(f"✗ Failed to initialize attributes: {e}")
            cls._initialized = False
            return False
    
    @classmethod
    def ensure_initialized(cls) -> bool:
        """
        Ensure attributes are initialized. Can be called at runtime.
        Returns True if attributes exist and are accessible.
        """
        if not cls._initialized:
            return cls.initialize_default_attributes()
        return True
    
    @classmethod
    def get_all_attributes(cls) -> List[JobAttribute]:
        """
        Get all attribute definitions with lazy initialization and caching.
        Ensures attributes are seeded if database is empty.
        Raises RuntimeError if no attributes can be loaded.
        """
        # Check cache first
        if cls._cached_attributes is not None and cls._initialized:
            return cls._cached_attributes
        
        # Ensure database is accessible
        db = cls._get_db()
        if db is None:
            raise RuntimeError(
                "MongoDB connection not available. "
                "Please check your MONGO_URI configuration."
            )
        
        # Check if we need to seed
        existing_count = db.job_attributes.count_documents({})
        if existing_count == 0:
            print("⚡ Lazy-initializing job attributes on first access")
            cls.initialize_default_attributes()
        
        # Load from database
        attributes = JobAttribute.get_all_attributes()
        
        if not attributes:
            raise RuntimeError(
                "No job attributes found after initialization. "
                "Please check MongoDB connection and seed data."
            )
        
        cls._cached_attributes = attributes
        cls._initialized = True
        return attributes
    
    @classmethod
    def get_attribute(cls, attribute_key: str) -> Optional[JobAttribute]:
        """Get a specific attribute by key."""
        return JobAttribute.find_by_key(attribute_key)
    
    @classmethod
    def get_attributes_json(cls) -> List[Dict[str, Any]]:
        """Get all attributes as JSON-serializable list."""
        attributes = cls.get_all_attributes()
        return [attr.to_json() for attr in attributes]
    
    @classmethod
    def add_attribute(cls, attribute_key: str, display_name: str,
                      levels: List[Dict[str, str]]) -> JobAttribute:
        """
        Add a new attribute definition.
        
        Args:
            attribute_key: Unique key for the attribute
            display_name: Human-readable name
            levels: List of {'level_id': str, 'display_text': str}
        
        Returns:
            Created JobAttribute
        """
        # Validate levels format
        for level in levels:
            if 'level_id' not in level or 'display_text' not in level:
                raise ValueError("Each level must have 'level_id' and 'display_text'")
        
        # Check for existing
        existing = JobAttribute.find_by_key(attribute_key)
        if existing:
            raise ValueError(f"Attribute '{attribute_key}' already exists")
        
        attr = JobAttribute(
            attribute_key=attribute_key,
            display_name=display_name,
            levels=levels
        )
        attr.save()
        return attr
    
    @classmethod
    def update_attribute_levels(cls, attribute_key: str,
                                levels: List[Dict[str, str]]) -> JobAttribute:
        """
        Update levels for an existing attribute.
        Note: Should be done carefully as it affects experiment validity.
        """
        attr = JobAttribute.find_by_key(attribute_key)
        if not attr:
            raise ValueError(f"Attribute '{attribute_key}' not found")
        
        # Validate levels
        for level in levels:
            if 'level_id' not in level or 'display_text' not in level:
                raise ValueError("Each level must have 'level_id' and 'display_text'")
        
        attr.collection.update_one(
            {'attribute_key': attribute_key},
            {'$set': {'levels': levels}}
        )
        attr.levels = levels
        return attr
    
    @classmethod
    def get_attribute_statistics(cls) -> Dict[str, Any]:
        """
        Get statistics about attributes (useful for experiment design).
        """
        attributes = cls.get_all_attributes()
        
        total_combinations = 1
        for attr in attributes:
            total_combinations *= len(attr.levels)
        
        return {
            'attribute_count': len(attributes),
            'total_possible_combinations': total_combinations,
            'attributes': [{
                'key': attr.attribute_key,
                'name': attr.display_name,
                'level_count': len(attr.levels)
            } for attr in attributes]
        }
