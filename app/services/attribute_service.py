"""
Attribute Service - Manages job attributes for conjoint analysis
"""
from typing import List, Dict, Any, Optional
from app.models.job_attribute import JobAttribute, DEFAULT_JOB_ATTRIBUTES
from app import mongo


class AttributeService:
    """
    Service for managing conjoint job attributes.
    """
    
    @classmethod
    def initialize_default_attributes(cls):
        """
        Initialize default job attributes if not already present.
        Called on app startup.
        """
        try:
            for attr_data in DEFAULT_JOB_ATTRIBUTES:
                existing = JobAttribute.find_by_key(attr_data['attribute_key'])
                if not existing:
                    attr = JobAttribute(
                        attribute_key=attr_data['attribute_key'],
                        display_name=attr_data['display_name'],
                        levels=attr_data['levels']
                    )
                    attr.save()
        except Exception as e:
            # Log error but don't crash app
            print(f"Warning: Could not initialize attributes: {e}")
    
    @classmethod
    def get_all_attributes(cls) -> List[JobAttribute]:
        """Get all attribute definitions."""
        return JobAttribute.get_all_attributes()
    
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
