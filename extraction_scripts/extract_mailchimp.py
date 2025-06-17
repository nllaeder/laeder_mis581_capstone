import os
import requests
from google.cloud import secretmanager
import json

def get_secret(project_id: str, secret_id: str) -> dict | None:
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    try:
        response = client.access_secret_version(request={"name": name})
        payload = response.payload.data.decode("UTF-8")
        return json.loads(payload)
    except Exception as e:
        print(f"Could not retrieve or decode secret '{secret_id}': {e}")
        return None

def fetch_mailchimp_campaigns(user_id, project_id):
    secret_id = f"user_{user_id}_mailchimp_token"
    token_data = get_secret(project_id, secret_id)
    if not token_data:
        print(f"No token found for user {user_id}")
        return
    access_token = token_data.get('access_token')
    server_prefix = token_data.get('server_prefix')
    if not access_token or not server_prefix:
        print("Missing access_token or server_prefix in token data.")
        return
    url = f"https://{server_prefix}.api.mailchimp.com/3.0/campaigns"
    headers = {"Authorization": f"OAuth {access_token}"}
    params = {"count": 10, "offset": 0}  # Fetch a sample
    resp = requests.get(url, headers=headers, params=params)
    if resp.status_code != 200:
        print(f"Mailchimp API error: {resp.status_code} {resp.text}")
        return
    data = resp.json()
    total_items = data.get('total_items', 0)
    campaigns = data.get('campaigns', [])
    print(f"Total campaigns: {total_items}")
    if campaigns:
        print("Sample campaign schema:")
        print(json.dumps(campaigns[0], indent=2))
    else:
        print("No campaigns found.")

if __name__ == "__main__":
    # Example usage: set these values appropriately
    user_id = os.environ.get("MAILCHIMP_TEST_USER_ID")
    project_id = os.environ.get("GOOGLE_PROJECT_ID")
    if not user_id or not project_id:
        print("Set MAILCHIMP_TEST_USER_ID and GOOGLE_PROJECT_ID in your environment.")
    else:
        fetch_mailchimp_campaigns(user_id, project_id)
