"""
Jack & Jill Conjoint Experiment Application
Flask application factory with MongoDB integration
"""
from flask import Flask
from flask_pymongo import PyMongo

mongo = PyMongo()


def create_app(config_name='default'):
    """Application factory pattern for Flask app creation."""
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    
    # Load configuration
    from app.config import config
    app.config.from_object(config[config_name])
    
    # Initialize MongoDB
    mongo.init_app(app)
    
    # Register blueprints
    from app.routes.api import api_bp
    from app.routes.views import views_bp
    
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(views_bp)
    
    # Initialize default job attributes if not exists
    with app.app_context():
        from app.services.attribute_service import AttributeService
        AttributeService.initialize_default_attributes()
    
    return app
