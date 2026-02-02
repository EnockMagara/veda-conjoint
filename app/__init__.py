"""
Veda Conjoint Experiment Application
Flask application factory with MongoDB integration
"""
from flask import Flask
from flask_pymongo import PyMongo
import os

mongo = PyMongo()


def create_app(config_name='default'):
    """Application factory pattern for Flask app creation."""
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    
    # Load configuration
    from app.config import config
    app.config.from_object(config[config_name])
    
    # Debug: Log MongoDB URI (masked)
    mongo_uri = app.config.get('MONGO_URI', 'NOT SET')
    if mongo_uri and mongo_uri != 'NOT SET':
        # Mask password for logging
        masked_uri = mongo_uri.split('@')[0][:20] + '...' if '@' in mongo_uri else mongo_uri[:30] + '...'
        print(f"🔗 MongoDB URI configured: {masked_uri}")
    else:
        print("⚠️ MONGO_URI not configured!")
    
    # Initialize MongoDB
    mongo.init_app(app)
    
    # Register blueprints
    from app.routes.api import api_bp
    from app.routes.views import views_bp
    
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(views_bp)
    
    # Verify MongoDB connection and initialize attributes
    with app.app_context():
        try:
            # Test connection by listing collections
            if mongo.db is not None:
                collections = mongo.db.list_collection_names()
                print(f"✅ MongoDB connected. Collections: {collections}")
            else:
                print("⚠️ mongo.db is None - connection may not be ready")
        except Exception as e:
            print(f"⚠️ MongoDB connection test failed: {e}")
        
        # Initialize default job attributes
        from app.services.attribute_service import AttributeService
        AttributeService.initialize_default_attributes()
    
    return app
