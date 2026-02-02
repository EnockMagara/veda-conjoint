"""
Configuration classes for different environments
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'jack-and-jill-secret-key-2024'
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/jack_and_jill_conjoint'
    
    # Conjoint experiment settings
    CONJOINT_ROUNDS = 5  # Number of A/B comparisons per session (3-5 per participant)
    SESSION_TIMEOUT_MINUTES = 60
    
    # Customizable branding
    ASSISTANT_NAME = os.environ.get('ASSISTANT_NAME') or 'Jill'
    COMPANY_NAME = os.environ.get('COMPANY_NAME') or 'Veda-'
    
    # Chat flow settings
    CHAT_QUESTIONS = [
        {
            'id': 'welcome',
            'type': 'info',
            'message': "Hi! I'm Jill, the AI assistant for Veda. I'll ask you a few quick questions about the kind of roles and employers you're looking for, which should take about three minutes. Based on your answers, I'll be able to help identify roles that will be well suited to what you are looking for. Let's get started."
        },
        {
            'id': 'email',
            'type': 'text',
            'message': "Please confirm your email address.",
            'placeholder': 'Enter your email address'
        },
        {
            'id': 'name',
            'type': 'text',
            'message': "Great! What's your name?",
            'placeholder': 'Enter your full name'
        },
        {
            'id': 'zip_code',
            'type': 'text',
            'message': "And your ZIP code?",
            'placeholder': 'Enter your ZIP code'
        },
        {
            'id': 'position_type',
            'type': 'text',
            'message': "What kind of position are you looking for? (e.g. Marketing Manager in tech)",
            'placeholder': 'Describe the position you\'re seeking'
        },
        {
            'id': 'work_preference',
            'type': 'choice',
            'message': "How would you ideally like to work?",
            'options': [
                {'value': 'remote', 'label': 'Remote'},
                {'value': 'hybrid', 'label': 'Hybrid'},
                {'value': 'in_person', 'label': 'In-person'},
                {'value': 'no_preference', 'label': 'No strong preference'}
            ]
        },
        {
            'id': 'salary_range',
            'type': 'choice',
            'message': "What salary range are you targeting?",
            'options': [
                {'value': 'below_50k', 'label': 'Below $50,000'},
                {'value': '50k_75k', 'label': '$50,000 - $75,000'},
                {'value': '75k_100k', 'label': '$75,000 - $100,000'},
                {'value': '100k_150k', 'label': '$100,000 - $150,000'},
                {'value': 'above_150k', 'label': '$150,000+'},
                {'value': 'flexible', 'label': "I'm flexible"}
            ]
        },
        {
            'id': 'conjoint',
            'type': 'conjoint',
            'message': "Now I'd like to understand your job preferences better. Which company would you be more likely to apply to?"
        }
    ]


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = True
    TESTING = True
    MONGO_URI = 'mongodb://localhost:27017/jack_and_jill_test'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
