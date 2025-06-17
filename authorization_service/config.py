# authorization_service/config.py
import os
from dotenv import load_dotenv
from google.cloud import secretmanager

# Load environment variables from .env file
load_dotenv()

def get_secret(secret_id, project_id=None):
    project_id = project_id or os.environ.get("GOOGLE_PROJECT_ID")
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

def store_secret(secret_id, secret_value, project_id=None):
    project_id = project_id or os.environ.get("GOOGLE_PROJECT_ID")
    client = secretmanager.SecretManagerServiceClient()
    parent = f"projects/{project_id}"
    # Create the secret if it doesn't exist
    try:
        client.create_secret(
            request={
                "parent": parent,
                "secret_id": secret_id,
                "secret": {"replication": {"automatic": {}}},
            }
        )
    except Exception:
        pass  # Secret may already exist
    # Add a new version with the secret value
    client.add_secret_version(
        request={
            "parent": f"{parent}/secrets/{secret_id}",
            "payload": {"data": secret_value.encode("UTF-8")},
        }
    )

class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'a-very-strong-dev-secret-key'
    GCP_PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT')

    # --- OAuth Credentials from Environment/Secret Manager ---
    # For Google Sign-In
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')

    # For Mailchimp
    MAILCHIMP_CLIENT_ID = os.environ.get('MAILCHIMP_CLIENT_ID')
    MAILCHIMP_CLIENT_SECRET = os.environ.get('MAILCHIMP_CLIENT_SECRET')

    # For Constant Contact
    CONSTANT_CONTACT_CLIENT_ID = os.environ.get('CONSTANT_CONTACT_CLIENT_ID')
    CONSTANT_CONTACT_CLIENT_SECRET = os.environ.get('CONSTANT_CONTACT_CLIENT_SECRET')

    @staticmethod
    def init_app(app):
        # This allows Authlib to work with http://localhost for development.
        if os.environ.get('OAUTHLIB_INSECURE_TRANSPORT'):
            os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    # Ensure Authlib can run insecurely on HTTP for local development
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    # Production should always use HTTPS, so OAUTHLIB_INSECURE_TRANSPORT should not be set.

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}