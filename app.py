import os
import requests
import json
import uuid
from urllib.parse import urlparse, parse_qs
from flask import Flask, request, redirect, session, url_for, render_template
from google.cloud import secretmanager
from dotenv import load_dotenv

load_dotenv() # Load variables from .env file

app = Flask(__name__)
app.secret_key = os.urandom(24) # Needed for session management

# --- Configuration ---
# Load from environment variables. Ensure these are set in your environment.
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
MAILCHIMP_CLIENT_ID = os.environ.get("MAILCHIMP_CLIENT_ID")
MAILCHIMP_CLIENT_SECRET = os.environ.get("MAILCHIMP_CLIENT_SECRET")

# --- Diagnostic Prints ---
print("-" * 40)
print("Checking environment variables...")
print(f"GCP_PROJECT_ID loaded: {GCP_PROJECT_ID is not None}")
print(f"MAILCHIMP_CLIENT_ID loaded: {MAILCHIMP_CLIENT_ID is not None}")
print(f"MAILCHIMP_CLIENT_SECRET loaded: {MAILCHIMP_CLIENT_SECRET is not None}")
print("If any are False, check your .env file.")
print("-" * 40)

# IMPORTANT: This must match the "Redirect URI" in your Mailchimp OAuth App settings.
# For local testing, it will be http://127.0.0.1:5000/callback
REDIRECT_URI = "http://34.74.242.84:5000/callback" 

def store_secret(project_id: str, secret_id: str, payload: dict):
    """Stores a secret in Google Cloud Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    parent = f"projects/{project_id}"
    secret_name = f"{parent}/secrets/{secret_id}"

    try:
        client.get_secret(request={"name": secret_name})
    except Exception:
        client.create_secret(
            request={
                "parent": parent,
                "secret_id": secret_id,
                "secret": {"replication": {"automatic": {}}},
            }
        )
    payload_bytes = json.dumps(payload).encode("UTF-8")
    client.add_secret_version(
        request={"parent": secret_name, "payload": {"data": payload_bytes}}
    )
    print(f"Successfully stored token in secret: {secret_id}")


@app.route("/")
def index():
    """Homepage with a link to start the authorization process."""
    return render_template('index.html')


@app.route("/authorize")
def authorize():
    """Redirects user to Mailchimp for authorization."""
    if not all([GCP_PROJECT_ID, MAILCHIMP_CLIENT_ID, MAILCHIMP_CLIENT_SECRET]):
        return "Error: Environment variables are not set.", 500

    # Create a state token to prevent CSRF attacks.
    state = str(uuid.uuid4())
    session['state'] = state

    auth_url = (
        f"https://login.mailchimp.com/oauth2/authorize?"
        f"response_type=code&client_id={MAILCHIMP_CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}&state={state}"
    )
    return redirect(auth_url)


@app.route("/callback")
def callback():
    """Handles the callback from Mailchimp after authorization."""
    # --- 1. Security Check: Validate State ---
    if request.args.get('state') != session.pop('state', None):
        return "Error: State mismatch. This could be a sign of a CSRF attack.", 400

    # --- 2. Get Authorization Code ---
    auth_code = request.args.get("code")
    if not auth_code:
        return "Error: No authorization code provided by Mailchimp.", 400

    # --- 3. Exchange Code for Access Token ---
    token_url = "https://login.mailchimp.com/oauth2/token"
    token_data = {
        "grant_type": "authorization_code",
        "client_id": MAILCHIMP_CLIENT_ID,
        "client_secret": MAILCHIMP_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "code": auth_code,
    }
    response = requests.post(token_url, data=token_data)
    if response.status_code != 200:
        return f"Error exchanging code for token: {response.text}", 500
    token_payload = response.json()

    # --- 4. Get Server Prefix (Metadata) ---
    metadata_url = "https://login.mailchimp.com/oauth2/metadata"
    headers = {"Authorization": f"OAuth {token_payload['access_token']}"}
    metadata_response = requests.get(metadata_url, headers=headers)
    if metadata_response.status_code != 200:
        return f"Error getting metadata: {metadata_response.text}", 500
    metadata_payload = metadata_response.json()

    # --- 5. Combine and Store Token ---
    full_token_data = {**token_payload, "dc": metadata_payload.get("dc")}
    secret_id = "mailchimp_oauth_token"  # Using a fixed name for simplicity
    
    if not GCP_PROJECT_ID:
        return "Error: GCP_PROJECT_ID environment variable not set.", 500
        
    try:
        store_secret(GCP_PROJECT_ID, secret_id, full_token_data)
    except Exception as e:
        return f"Error storing secret in GCP Secret Manager: {e}", 500

    return "<h1>Success!</h1><p>Authorization complete. Your Mailchimp token has been securely stored.</p>"


if __name__ == "__main__":
    # Note: This is for local development only.
    # For production, use a proper WSGI server like Gunicorn.
    app.run(host='0.0.0.0', port=5000, debug=True) 