# authorization_service/app/__init__.py
from flask import Flask, session
from authlib.integrations.flask_client import OAuth
from flask_login import LoginManager, UserMixin
from flask_wtf.csrf import CSRFProtect
from config import config

csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = 'auth.login_google' # Redirect to google login if user is not authenticated
oauth = OAuth()

# A simple user class for Flask-Login
class User(UserMixin):
    def __init__(self, id, name=None, email=None):
        self.id = id
        self.name = name
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    # In this app, user details are stored in the session.
    # A real-world app might query a database here.
    user_info = session.get('user_info')
    if user_info and user_info['id'] == user_id:
        return User(id=user_info['id'], name=user_info.get('name'), email=user_info.get('email'))
    return None

def create_app(config_name='default'):
    """Application factory function."""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # Initialize extensions
    csrf.init_app(app)
    login_manager.init_app(app)
    oauth.init_app(app)

    # --- Register OAuth Providers ---
    # Google Sign-In
    oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )
    # Constant Contact
    oauth.register(
        name='constantcontact',
        client_id=app.config['CONSTANT_CONTACT_CLIENT_ID'],
        client_secret=app.config['CONSTANT_CONTACT_CLIENT_SECRET'],
        access_token_url='https://authz.constantcontact.com/oauth2/default/v1/token',
        authorize_url='https://authz.constantcontact.com/oauth2/default/v1/authorize',
        client_kwargs={'scope': 'contact_data offline_access'},
    )
    # Mailchimp
    oauth.register(
        name='mailchimp',
        client_id=app.config['MAILCHIMP_CLIENT_ID'],
        client_secret=app.config['MAILCHIMP_CLIENT_SECRET'],
        access_token_url='https://login.mailchimp.com/oauth2/token',
        authorize_url='https://login.mailchimp.com/oauth2/authorize',
        client_kwargs={'scope': 'contacts_read campaigns_read'},
    )

    # Register blueprints
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    return app