# authorization_service/app/services/gcp.py
from google.cloud import secretmanager
from google.api_core.exceptions import NotFound
import json

def store_secret(project_id: str, secret_id: str, payload: dict):
    """
    Creates a secret if it doesn't exist, then adds a new version with a JSON payload.
    """
    client = secretmanager.SecretManagerServiceClient()
    parent = f"projects/{project_id}"
    secret_name = f"{parent}/secrets/{secret_id}"

    try:
        client.get_secret(request={"name": secret_name})
    except NotFound:
        client.create_secret(
            request={
                "parent": parent,
                "secret_id": secret_id,
                "secret": {"replication": {"automatic": {}}},
            }
        )

    payload_bytes = json.dumps(payload).encode("UTF-8")
    version = client.add_secret_version(
        request={"parent": secret_name, "payload": {"data": payload_bytes}}
    )
    return version.name

def get_secret(project_id: str, secret_id: str) -> dict | None:
    """
    Retrieves the latest version of a secret from Google Secret Manager.
    Returns the secret payload as a dictionary.
    """
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    try:
        response = client.access_secret_version(request={"name": name})
        payload = response.payload.data.decode("UTF-8")
        return json.loads(payload)
    except (NotFound, json.JSONDecodeError) as e:
        print(f"Could not retrieve or decode secret '{secret_id}': {e}")
        return None