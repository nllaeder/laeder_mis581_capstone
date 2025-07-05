import os
import requests
import json
import uuid
import base64
from urllib.parse import urlparse, parse_qs
from flask import Flask, request, redirect, session, url_for, render_template
from google.cloud import secretmanager
from dotenv import load_dotenv

load_dotenv() # Load variables from .env file

app = Flask(__name__)
app.secret_key = os.urandom(24) # Needed for session management. CHANGE THIS IN PRODUCTION TO A LONG, RANDOM STRING FROM ENV.

# --- Configuration ---
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
MAILCHIMP_CLIENT_ID = os.environ.get("MAILCHIMP_CLIENT_ID")
MAILCHIMP_CLIENT_SECRET = os.environ.get("MAILCHIMP_CLIENT_SECRET")
CONSTANT_CONTACT_CLIENT_ID = os.environ.get("CONSTANT_CONTACT_CLIENT_ID")
CONSTANT_CONTACT_CLIENT_SECRET = os.environ.get("CONSTANT_CONTACT_CLIENT_SECRET")

# IMPORTANT: This must match the "Redirect URI" in your App settings AND Flask route definition.
REDIRECT_URI = "http://34.74.242.84:5000/callback" 
CC_REDIRECT_URI = "http://34.74.242.84:5000/cc_callback/"

# --- NEW: Import Firestore and Initialize Firestore DB (from previous plan) ---
# This part assumes you'll re-integrate Firestore storing later. For now, it's commented out
# to keep focus on the state mismatch.
# from google.cloud import firestore
# db_firestore = firestore.Client(project=GCP_PROJECT_ID)

# --- NEW/MODIFIED: store_secret function will be kept for now as it's used in the code ---
def store_secret(project_id: str, secret_id: str, payload: dict):
    """Stores a secret in Google Cloud Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    parent = f"projects/{project_id}"
    secret_name = f"{parent}/secrets/{secret_id}"

    try:
        client.get_secret(request={"name": secret_name})
    except Exception:
        print(f"Secret {secret_id} not found. Creating it now.")
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
    print(f"Successfully stored/updated token in secret: {secret_id}")

# --- NEW/MODIFIED: Function to store tokens in Firestore (from previous plan, kept for completeness) ---
# This function is not currently called in the provided app.py but would be used if storing to Firestore.
# def store_oauth_token_in_firestore(user_id: str, provider: str, token_payload: dict):
#     app_id_flask = os.environ.get("FLASK_APP_ID", "default-app-id-flask")
#     doc_ref = db_firestore.collection('artifacts').document(app_id_flask).collection('users').document(user_id).collection('tokens').document('oauth')
#
#     current_data = doc_ref.get()
#     if current_data.exists:
#         data = current_data.to_dict()
#     else:
#         data = {}
#
#     data[provider] = token_payload
#     doc_ref.set(data)
#     print(f"Successfully stored {provider} token for user {user_id} in Firestore.")


@app.route("/")
def index():
    """Homepage with links to start the authorization process."""
    return render_template('index.html')


@app.route("/authorize")
def authorize():
    """Redirects user to Mailchimp for authorization. Now accepts a peer id."""
    ### CHANGE START ###
    peer_id = request.args.get('peer', 'unknown') # e.g., /authorize?peer=2
    if not all([GCP_PROJECT_ID, MAILCHIMP_CLIENT_ID, MAILCHIMP_CLIENT_SECRET]):
        return "Error: Environment variables are not set.", 500

    state_uuid = str(uuid.uuid4())
    state = f"{state_uuid}|peer_id={peer_id}" # Embed peer_id in the state
    session['state'] = state
    print(f"DEBUG: Mailchimp /authorize set session['state'] to: {session['state']}") # TEMP PRINT
    ### CHANGE END ###

    auth_url = (
        f"https://login.mailchimp.com/oauth2/authorize?"
        f"response_type=code&client_id={MAILCHIMP_CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}&state={state}"
    )
    return redirect(auth_url)


@app.route("/cc_authorize")
def cc_authorize():
    """Redirects user to Constant Contact for authorization. Now accepts a peer id."""
    ### CHANGE START ###
    peer_id = request.args.get('peer', 'unknown') # e.g., /cc_authorize?peer=1
    if not all([GCP_PROJECT_ID, CONSTANT_CONTACT_CLIENT_ID, CONSTANT_CONTACT_CLIENT_SECRET]):
        return "Error: Constant Contact environment variables are not set.", 500

    # --- DIAGNOSTIC PRINT for Client ID ---
    print(f"--- Using Constant Contact Client ID: {CONSTANT_CONTACT_CLIENT_ID} ---")
    # ---

    state_uuid = str(uuid.uuid4())
    state = f"{state_uuid}|peer_id={peer_id}" # Embed peer_id in the state
    session['cc_state'] = state
    print(f"DEBUG: Constant Contact /cc_authorize set session['cc_state'] to: {session['cc_state']}") # TEMP PRINT
    ### CHANGE END ###

    auth_url = (
        f"https://authz.constantcontact.com/oauth2/default/v1/authorize?"
        f"response_type=code&client_id={CONSTANT_CONTACT_CLIENT_ID}"
        f"&redirect_uri={CC_REDIRECT_URI}&scope=account_read%20contact_data%20campaign_data%20offline_access&state={state}" # Updated scope
    )
    return redirect(auth_url)


@app.route("/callback")
def callback():
    """Handles the callback from Mailchimp after authorization."""
    # --- 1. Security Check: Validate State ---
    state_from_mc = request.args.get('state')
    state_from_session = session.pop('state', None)

    print(f"DEBUG: Mailchimp /callback received state_from_mc: {state_from_mc}")    # TEMP PRINT
    print(f"DEBUG: Mailchimp /callback retrieved state_from_session: {state_from_session}") # TEMP PRINT

    if not state_from_mc or state_from_mc != state_from_session:
        return "Error: State mismatch. This could be a sign of a CSRF attack.", 400

    # Extract peer_id from the state string
    try:
        peer_id = state_from_mc.split('|peer_id=')[1]
    except (IndexError, TypeError):
        peer_id = "unknown"
    
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
    # Explicitly setting Content-Type for Mailchimp
    headers = { 
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json" # Added Accept header as per previous recommendation
    }
    response = requests.post(token_url, headers=headers, data=token_data)
    if response.status_code != 200:
        return f"Error exchanging code for token: {response.status_code} {response.text}", 500
    token_payload = response.json()

    # --- DIAGNOSTIC PRINT ---
    print("--- FRESH MAILCHIMP TOKEN DATA ---")
    print(json.dumps(token_payload, indent=2))
    print("----------------------------------")

    # --- 4. Get Server Prefix (Metadata) ---
    try:
        metadata_url = "https://login.mailchimp.com/oauth2/metadata"
        headers = {"Authorization": f"OAuth {token_payload['access_token']}"}
        metadata_response = requests.get(metadata_url, headers=headers)
        metadata_response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        token_payload['dc'] = metadata_response.json()["dc"]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Mailchimp metadata: {e}") # Changed to print for debugging
        # Do not return 500 here, allow the flow to continue storing main token
        token_payload['dc'] = 'error_fetching_dc' # Add a placeholder for troubleshooting
    except KeyError:
        print("Error: 'dc' (server prefix) not found in Mailchimp metadata response.") # Changed to print for debugging
        token_payload['dc'] = 'dc_not_found' # Add a placeholder for troubleshooting

    # --- 5. Combine and Store Token ---
    secret_id = f"peer{peer_id}_mailchimp_token"
    print(f"Received tokens for Mailchimp peer: {peer_id}. Storing in secret: {secret_id}")

    if not GCP_PROJECT_ID:
        return "Error: GCP_PROJECT_ID environment variable not set.", 500

    try:
        store_secret(GCP_PROJECT_ID, secret_id, token_payload)
    except Exception as e:
        return f"Error storing secret in GCP Secret Manager: {e}", 500

    return "<h1>Success!</h1><p>Authorization complete. Your Mailchimp token has been securely stored.</p>"


@app.route("/cc_callback/") # Retaining trailing slash based on last successful Constant Contact redirect
def cc_callback():
    """Handles the callback from Constant Contact after authorization."""
    # --- 1. Security Check: Validate State ---
    state_from_cc = request.args.get('state')
    state_from_session = session.pop('cc_state', None)
    
    print(f"DEBUG: Constant Contact /cc_callback received state_from_cc: {state_from_cc}")    # TEMP PRINT
    print(f"DEBUG: Constant Contact /cc_callback retrieved state_from_session: {state_from_session}") # TEMP PRINT

    if not state_from_cc or state_from_cc != state_from_session:
        return "Error: State mismatch. This could be a sign of a CSRF attack.", 400

    # Extract peer_id from the state string
    try:
        peer_id = state_from_cc.split('|peer_id=')[1]
    except (IndexError, TypeError):
        peer_id = "unknown"

    # --- 2. Get Authorization Code ---
    auth_code = request.args.get("code")
    if not auth_code:
        return "Error: No authorization code provided by Constant Contact.", 400

    # --- 3. Exchange Code for Access Token ---
    token_url = "https://authz.constantcontact.com/oauth2/default/v1/token"
    auth_string = f"{CONSTANT_CONTACT_CLIENT_ID}:{CONSTANT_CONTACT_CLIENT_SECRET}"
    auth_header = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json" # Added Accept header as per previous recommendation
    }
    token_data = {
        "grant_type": "authorization_code",
        "redirect_uri": CC_REDIRECT_URI,
        "code": auth_code,
    }
    
    response = requests.post(token_url, headers=headers, data=token_data)
    
    if response.status_code != 200:
        return f"Error exchanging code for token: {response.status_code} {response.text}", 500
        
    token_payload = response.json()

    # THIS IS THE CRITICAL DIAGNOSTIC PRINT
    print("--- FRESH CONSTANT CONTACT TOKEN DATA ---")
    print(json.dumps(token_payload, indent=2))
    print("-----------------------------------------")

    # --- 4. Store Token ---
    # Make the secret name dynamic based on the peer
    secret_id = f"peer{peer_id}_constant_contact_token"
    print(f"Received tokens for Constant Contact peer: {peer_id}. Storing in secret: {secret_id}")
    
    if not GCP_PROJECT_ID:
        return "Error: GCP_PROJECT_ID environment variable not set.", 500
        
    try:
        store_secret(GCP_PROJECT_ID, secret_id, token_payload)
    except Exception as e:
        return f"Error storing secret in GCP Secret Manager: {e}", 500

    return "<h1>Success!</h1><p>Authorization complete. Your Constant Contact token has been securely stored.</p>"


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False) # <--- ADDED use_reloader=False
