"""
Veda Conjoint Experiment Application
Flask application factory with MongoDB integration
"""
from flask import Flask
from flask_pymongo import PyMongo
from pymongo import MongoClient
from urllib.parse import urlparse
import os

mongo = PyMongo()

# Direct MongoDB client for operations outside request context
_direct_client = None
_direct_db = None


def get_db():
    """
    Get MongoDB database, works both in and out of request context.
    Uses Flask-PyMongo's connection when available, falls back to direct client.
    """
    global _direct_client, _direct_db
    
    # Try Flask-PyMongo first (preferred in request context)
    if mongo.db is not None:
        return mongo.db
    
    # Fallback to direct client
    if _direct_db is not None:
        return _direct_db
    
    return None


def _extract_db_name(mongo_uri: str) -> str:
    """
    Extract database name from MongoDB URI.
    Handles URIs like: mongodb://user:pass@host:port/dbname?options
    """
    try:
        parsed = urlparse(mongo_uri)
        # Path contains /dbname - strip leading slash
        db_name = parsed.path.lstrip('/')
        # Remove any query parameters that might have slipped through
        if '?' in db_name:
            db_name = db_name.split('?')[0]
        # Default if empty
        if not db_name or '.' in db_name:  # Invalid db name
            db_name = 'veda_conjoint'
        return db_name
    except Exception:
        return 'veda_conjoint'


def create_app(config_name='default'):
    """Application factory pattern for Flask app creation."""
    global _direct_client, _direct_db
    
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    
    # Load configuration
    from app.config import config
    app.config.from_object(config[config_name])
    
    # Get MongoDB URI
    mongo_uri = app.config.get('MONGO_URI', '')
    
    if mongo_uri:
        # Mask password for logging
        masked_uri = mongo_uri.split('@')[-1] if '@' in mongo_uri else mongo_uri[:30]
        print(f"🔗 MongoDB URI: ...@{masked_uri}")
        
        # Extract database name from URI
        db_name = _extract_db_name(mongo_uri)
        print(f"📦 Database name: {db_name}")
        
        # Initialize direct MongoDB connection first
        try:
            _direct_client = MongoClient(mongo_uri)
            _direct_db = _direct_client[db_name]
            
            # Test connection
            _direct_client.server_info()
            print(f"✅ Direct MongoDB connection established to '{db_name}'")
        except Exception as e:
            print(f"⚠️ Direct MongoDB connection failed: {e}")
            _direct_client = None
            _direct_db = None
    else:
        print("⚠️ MONGO_URI not configured!")
    
    # Initialize Flask-PyMongo (for request context usage)
    mongo.init_app(app)
    
    # Register blueprints
    from app.routes.api import api_bp
    from app.routes.views import views_bp
    
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(views_bp)
    
    # Initialize default job attributes using direct connection
    if _direct_db is not None:
        try:
            existing_count = _direct_db.job_attributes.count_documents({})
            if existing_count == 0:
                from app.models.job_attribute import DEFAULT_JOB_ATTRIBUTES
                for attr_data in DEFAULT_JOB_ATTRIBUTES:
                    _direct_db.job_attributes.insert_one({
                        'attribute_key': attr_data['attribute_key'],
                        'display_name': attr_data['display_name'],
                        'levels': attr_data['levels']
                    })
                print(f"✓ Seeded {len(DEFAULT_JOB_ATTRIBUTES)} default job attributes")
            else:
                print(f"✓ Found {existing_count} existing job attributes")
        except Exception as e:
            print(f"⚠️ Failed to initialize attributes: {e}")
    
    return app
