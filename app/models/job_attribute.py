"""
JobAttribute Model - Defines attribute dimensions and levels for conjoint analysis
"""
from datetime import datetime
from bson import ObjectId
from app.models.base import BaseModel


class JobAttribute(BaseModel):
    """
    JobAttribute model for conjoint attribute definitions.
    
    Fields:
        - attribute_key (string)
        - display_name (string) - human-readable name
        - levels (array of objects)
            - level_id (string)
            - display_text (string)
    
    Example:
        attribute_key: 'company_size'
        levels: [
            {'level_id': 'small', 'display_text': '1-50 employees'},
            {'level_id': 'medium', 'display_text': '51-500 employees'},
            {'level_id': 'large', 'display_text': '500+ employees'}
        ]
    """
    
    collection_name = 'job_attributes'
    
    def __init__(self, attribute_key: str, display_name: str, levels: list):
        self.attribute_key = attribute_key
        self.display_name = display_name
        self.levels = levels  # [{'level_id': str, 'display_text': str}, ...]
        self.created_at = datetime.utcnow()
        self.id = None
    
    @classmethod
    def find_by_key(cls, attribute_key: str):
        """Find attribute by key."""
        return cls.find_one({'attribute_key': attribute_key})
    
    @classmethod
    def get_all_attributes(cls):
        """Get all attribute definitions."""
        return cls.find_many({})
    
    def get_level_text(self, level_id: str) -> str:
        """Get display text for a level ID."""
        for level in self.levels:
            if level['level_id'] == level_id:
                return level['display_text']
        return level_id
    
    @classmethod
    def ensure_indexes(cls):
        """Create indexes for the collection."""
        instance = cls.__new__(cls)
        instance.collection.create_index('attribute_key', unique=True)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'attribute_key': self.attribute_key,
            'display_name': self.display_name,
            'levels': self.levels,
            'created_at': self.created_at
        }
    
    def to_json(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        return {
            'id': str(self.id) if self.id else None,
            'attribute_key': self.attribute_key,
            'display_name': self.display_name,
            'levels': self.levels,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# Default job attributes for conjoint analysis - matches company comparison card format
DEFAULT_JOB_ATTRIBUTES = [
    {
        'attribute_key': 'company_description',
        'display_name': 'Company description',
        'levels': [
            {'level_id': 'tech_software', 'display_text': 'A technology company that develops software solutions to help organizations manage processes more efficiently and scale their operations.'},
            {'level_id': 'business_services', 'display_text': 'A business services firm that provides operational and advisory solutions to help organizations improve performance and manage complex projects.'},
            {'level_id': 'financial_services', 'display_text': 'A financial services company that provides investment management and advisory services to help clients grow and protect their wealth.'},
            {'level_id': 'healthcare_tech', 'display_text': 'A healthcare technology company that develops digital solutions to improve patient outcomes and streamline clinical operations.'}
        ]
    },
    {
        'attribute_key': 'company_size',
        'display_name': 'Company size',
        'levels': [
            {'level_id': 'small', 'display_text': '50-100 employees'},
            {'level_id': 'medium', 'display_text': '100-500 employees'},
            {'level_id': 'large', 'display_text': '500+ employees'}
        ]
    },
    {
        'attribute_key': 'compensation',
        'display_name': 'Compensation',
        'levels': [
            {'level_id': 'market_aligned', 'display_text': 'Market-aligned'},
            {'level_id': 'competitive', 'display_text': 'Competitive for the market'},
            {'level_id': 'above_market', 'display_text': 'Above market rate'}
        ]
    },
    {
        'attribute_key': 'location',
        'display_name': 'Location',
        'levels': [
            {'level_id': 'remote', 'display_text': 'Remote'},
            {'level_id': 'mostly_office', 'display_text': 'Mostly in office'},
            {'level_id': 'hybrid', 'display_text': 'Hybrid'}
        ]
    },
    {
        'attribute_key': 'culture_values',
        'display_name': "Recent updates on the company's culture and values",
        'levels': [
            {
                'level_id': 'dei_current',
                'display_text': 'In the company\'s most recent annual public filing (10-K), it states: "We know advancing equality takes all of us, so we\'re partnering with our ecosystem to design better diversity, equity, and inclusion (DEI) strategies and build more diverse workforces."'
            },
            {
                'level_id': 'dei_prior',
                'display_text': 'In prior annual public filings (10-K), the company stated: "We know advancing equality takes all of us, so we\'re partnering with our ecosystem to design better diversity, equity, and inclusion (DEI) strategies and build more diverse workforces." This language does not appear in the company\'s most recent filing.'
            },
            {
                'level_id': 'dei_none',
                'display_text': 'The company has not made any public statements regarding diversity, equity, and inclusion (DEI) initiatives in their recent filings.'
            }
        ]
    }
]
