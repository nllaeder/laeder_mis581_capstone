# authorization_service/config.py
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'a-default-secret-key'
    GCP_PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT')

    # In production, these should be fetched from Secret Manager or set as env vars
    # during deployment. For local dev, they are loaded from .env
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    MAILCHIMP_CLIENT_ID = os.environ.get('MAILCHIMP_CLIENT_ID')
    MAILCHIMP_CLIENT_SECRET = os.environ.get('MAILCHIMP_CLIENT_SECRET')
    CONSTANT_CONTACT_CLIENT_ID = os.environ.get('CONSTANT_CONTACT_CLIENT_ID')
    CONSTANT_CONTACT_CLIENT_SECRET = os.environ.get('CONSTANT_CONTACT_CLIENT_SECRET')

    @staticmethod
    def init_app(app):
        # Allow OAuth lib to work with HTTP for local development
        if os.environ.get('OAUTHLIB_INSECURE_TRANSPORT'):
            os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


class DevelopmentConfig(Config):
    DEBUG = True
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


class ProductionConfig(Config):
    DEBUG = False
    # In production, ensure OAUTHLIB_INSECURE_TRANSPORT is NOT set


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}