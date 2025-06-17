import os
import requests
from urllib.parse import urlparse, parse_qs
from google.cloud import secretmanager
import json

# --- Configuration ---
# Load from environment variables or replace with your actual credentials
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
MAILCHIMP_CLIENT_ID = os.environ.get("MAILCHIMP_CLIENT_ID")
MAILCHIMP_CLIENT_SECRET = os.environ.get("MAILCHIMP_CLIENT_SECRET")

# This must match the "Redirect URI" in your Mailchimp OAuth App settings
REDIRECT_URI = "https://example.com/callback"

def store_secret(project_id: str, secret_id: str, payload: dict):
    """Stores a secret in Google Cloud Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    parent = f"projects/{project_id}"
    secret_name = f"{parent}/secrets/{secret_id}"

    # Create the secret if it doesn't exist
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

    # Add a new version with the JSON payload
    payload_bytes = json.dumps(payload).encode("UTF-8")
    client.add_secret_version(
        request={"parent": secret_name, "payload": {"data": payload_bytes}}
    )
    print(f"Successfully stored token in secret: {secret_id}")

def main():
    """Main function to run the authorization flow."""
    if not all([GCP_PROJECT_ID, MAILCHIMP_CLIENT_ID, MAILCHIMP_CLIENT_SECRET]):
        print("Error: Please set GCP_PROJECT_ID, MAILCHIMP_CLIENT_ID, and MAILCHIMP_CLIENT_SECRET environment variables.")
        return

    # 1. Generate the authorization URL
    auth_url = (
        f"https://login.mailchimp.com/oauth2/authorize?"
        f"response_type=code&client_id={MAILCHIMP_CLIENT_ID}&redirect_uri={REDIRECT_URI}"
    )

    print("-" * 80)
    print("STEP 1: Authorize with Mailchimp")
    print("\n  Please open the following URL in your web browser:")
    print(f"\n  {auth_url}\n")
    print("  After authorizing, Mailchimp will redirect you to a URL that starts with 'https://example.com/callback'.")
    print("-" * 80)

    # 2. Get the redirected URL from the user
    redirected_url = input("  Please paste the full redirected URL here and press Enter:\n  > ")

    # 3. Extract the authorization code from the URL
    try:
        query_params = parse_qs(urlparse(redirected_url).query)
        auth_code = query_params["code"][0]
    except (KeyError, IndexError):
        print("\nError: Could not find 'code' in the provided URL. Please try again.")
        return

    print("\nAuthorization code received. Exchanging it for an access token...")

    # 4. Exchange the authorization code for an access token
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
        print(f"\nError: Failed to get access token. Status: {response.status_code}, Response: {response.text}")
        return

    token_payload = response.json()
    print("Access token received!")

    # 5. Get server prefix (metadata) required for API calls
    metadata_url = "https://login.mailchimp.com/oauth2/metadata"
    headers = {"Authorization": f"OAuth {token_payload['access_token']}"}
    metadata_response = requests.get(metadata_url, headers=headers)
    
    if metadata_response.status_code != 200:
        print(f"\nError: Failed to get server prefix. Status: {metadata_response.status_code}, Response: {metadata_response.text}")
        return
        
    metadata_payload = metadata_response.json()
    
    # Combine token and metadata for storage
    full_token_data = {
        **token_payload,
        "dc": metadata_payload.get("dc") 
    }

    # 6. Store the token in GCP Secret Manager
    # We'll use a fixed name for simplicity, but you could make this dynamic
    secret_id = "mailchimp_oauth_token"
    store_secret(GCP_PROJECT_ID, secret_id, full_token_data)
    
    print("\n" + "="*80)
    print("Authorization complete! Your Mailchimp token is securely stored in GCP Secret Manager.")
    print("="*80)


if __name__ == "__main__":
    main() 