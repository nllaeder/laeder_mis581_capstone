# authorization_service/app/main/routes.py
from flask import render_template
from flask_login import current_user
from . import main

@main.route('/')
def index():
    """Serves the public homepage."""
    return render_template('index.html')

@main.route('/dashboard')
def dashboard():
    """Serves the user's private dashboard after login."""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login_google'))
    return render_template('dashboard.html', user=current_user)