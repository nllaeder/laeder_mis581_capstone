# authorization_service/app/auth/routes.py
from flask import redirect, url_for, flash, render_template, session, current_app, request
from flask_login import login_user, logout_user, login_required, current_user
from . import auth
from .. import oauth
from ..app_utils import User  # Corrected import path
from ..services.gcp import store_secret, get_secret
import time
import requests
import os


# --- Google Sign-In Routes ---
@auth.route('/login_google')
def login_google():
    """Redirects to Google's authentication page."""
    redirect_uri = url_for('auth.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth.route('/google/callback')
def google_callback():
    """Handles the callback from Google."""
    try:
        token = oauth.google.authorize_access_token()
        user_info = oauth.google.parse_id_token(token)

        # The user's unique Google ID
        user_id = user_info['sub']
        user_name = user_info.get('name')
        user_email = user_info.get('email')

        # Create a user object and store info in session
        user = User(id=user_id, name=user_name, email=user_email)
        session['user_info'] = {'id': user.id, 'name': user.name, 'email': user.email}

        login_user(user)
        flash("Successfully logged in with Google!", "success")
        return redirect(url_for('main.dashboard'))
    except Exception as e:
        flash(f"Google login failed: {e}", "error")
        return redirect(url_for('main.index'))


@auth.route('/logout')
@login_required
def logout():
    """Logs the user out."""
    logout_user()
    session.clear()
    flash("You have been successfully logged out.", "success")
    return redirect(url_for('main.index'))


# --- 3rd Party Connection Routes ---
@auth.route('/connect/<provider>')
@login_required
def connect_provider(provider):
    """Initiates OAuth flow for a third-party provider (Mailchimp or Constant Contact)."""
    if provider not in oauth._clients:
        flash(f"Invalid provider: {provider}", "error")
        return redirect(url_for('main.dashboard'))

    redirect_uri = url_for('auth.provider_callback', provider=provider, _external=True)
    return oauth._clients[provider].authorize_redirect(redirect_uri)


@auth.route('/callback/<provider>')
@login_required
def provider_callback(provider):
    """Handles the callback from third-party providers."""
    if provider not in oauth._clients:
        flash(f"Invalid provider: {provider}", "error")
        return redirect(url_for('main.dashboard'))

    try:
        token_data = oauth._clients[provider].authorize_access_token()

        # Prepare token data for storage
        token_to_store = {
            'access_token': token_data.get('access_token'),
            'refresh_token': token_data.get('refresh_token'),
            'expires_at': token_data.get('expires_at', int(time.time()) + token_data.get('expires_in', 3600)),
        }

        # Add provider-specific data
        if provider == 'mailchimp':
            # Mailchimp provides the server prefix in a separate field
            token_to_store['server_prefix'] = token_data.get('dc')

        # Define a unique secret ID linked to the user
        secret_id = f"user_{current_user.id}_{provider}_token"

        # Store the token securely in Secret Manager
        project_id = current_app.config['GCP_PROJECT_ID']
        store_secret(project_id, secret_id, token_to_store)

        return render_template('success.html', provider=provider.title(), secret_id=secret_id)

    except Exception as e:
        return render_template('error.html', provider=provider.title(), error=str(e))


@auth.route('/connect/mailchimp')
def connect_mailchimp():
    project_id = os.environ.get('GOOGLE_PROJECT_ID') or current_app.config.get('GCP_PROJECT_ID')
    client_id = get_secret(project_id, 'app_mc_client_id')
    redirect_uri = url_for('auth.mailchimp_callback', _external=True)
    auth_url = f'https://login.mailchimp.com/oauth2/authorize?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}'
    return redirect(auth_url)

@auth.route('/callback/mailchimp')
def mailchimp_callback():
    code = request.args.get('code')
    if not code:
        return 'Authorization failed', 400

    project_id = os.environ.get('GOOGLE_PROJECT_ID') or current_app.config.get('GCP_PROJECT_ID')
    client_id = get_secret(project_id, 'app_mc_client_id')
    client_secret = get_secret(project_id, 'app_mc_client_secret')
    redirect_uri = url_for('auth.mailchimp_callback', _external=True)

    # Exchange the authorization code for an access token
    token_url = 'https://login.mailchimp.com/oauth2/token'
    data = {
        'grant_type': 'authorization_code',
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'code': code
    }
    response = requests.post(token_url, data=data)
    if response.status_code != 200:
        return 'Failed to obtain access token', 400

    token_data = response.json()
    user_id = session.get('user_info', {}).get('id', 'anonymous')
    secret_id = f'user_{user_id}_mailchimp_token'
    store_secret(project_id, secret_id, token_data)
    return render_template('success.html', provider='Mailchimp', secret_id=secret_id)

@auth.route('/connect/constantcontact')
def connect_constantcontact():
    project_id = os.environ.get('GOOGLE_PROJECT_ID') or current_app.config.get('GCP_PROJECT_ID')
    client_id = get_secret(project_id, 'app_cc_client_id')
    redirect_uri = url_for('auth.constantcontact_callback', _external=True)
    auth_url = (
        f'https://authz.constantcontact.com/oauth2/default/v1/authorize?response_type=code'
        f'&client_id={client_id}&redirect_uri={redirect_uri}&scope=contact_data+offline_access'
    )
    return redirect(auth_url)

@auth.route('/callback/constantcontact')
def constantcontact_callback():
    code = request.args.get('code')
    if not code:
        return 'Authorization failed', 400

    project_id = os.environ.get('GOOGLE_PROJECT_ID') or current_app.config.get('GCP_PROJECT_ID')
    client_id = get_secret(project_id, 'app_cc_client_id')
    client_secret = get_secret(project_id, 'app_cc_client_secret')
    redirect_uri = url_for('auth.constantcontact_callback', _external=True)

    token_url = 'https://authz.constantcontact.com/oauth2/default/v1/token'
    data = {
        'grant_type': 'authorization_code',
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'code': code
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post(token_url, data=data, headers=headers)
    if response.status_code != 200:
        return 'Failed to obtain access token', 400

    token_data = response.json()
    user_id = session.get('user_info', {}).get('id', 'anonymous')
    secret_id = f'user_{user_id}_constantcontact_token'
    store_secret(project_id, secret_id, token_data)
    return render_template('success.html', provider='Constant Contact', secret_id=secret_id)