import os
import requests
import json
from google.cloud import secretmanager, bigquery
import io

# --- Configuration ---
# Load from environment variables or replace with your actual values
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
BIGQUERY_DATASET_ID = os.environ.get("BIGQUERY_DATASET_ID", "mailchimp_data")
BIGQUERY_TABLE_ID = os.environ.get("BIGQUERY_TABLE_ID", "campaigns")
SECRET_ID = "mailchimp_oauth_token" # The secret ID used in the authorization script

def get_secret(project_id: str, secret_id: str) -> dict | None:
    """Retrieves a secret from Google Cloud Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    try:
        response = client.access_secret_version(request={"name": name})
        payload = response.payload.data.decode("UTF-8")
        return json.loads(payload)
    except Exception as e:
        print(f"Error: Could not retrieve secret '{secret_id}'. Please run the authorization script first.")
        print(f"Details: {e}")
        return None

def load_data_to_bigquery(project_id: str, dataset_id: str, table_id: str, data: list):
    """Loads a list of dictionaries into a BigQuery table."""
    if not data:
        print("No data provided to load into BigQuery.")
        return

    client = bigquery.Client(project=project_id)
    dataset_ref = client.dataset(dataset_id)
    table_ref = dataset_ref.table(table_id)
    
    # Create dataset if it doesn't exist
    try:
        client.get_dataset(dataset_ref)
        print(f"Dataset '{dataset_id}' already exists.")
    except Exception:
        print(f"Creating dataset '{dataset_id}'...")
        client.create_dataset(dataset_ref)

    # Configure the job to create the table and infer the schema
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        autodetect=True,  # Infer schema from the data
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE, # Overwrite table
    )

    # Convert list of dicts to newline-delimited JSON
    data_as_json_str = "\n".join([json.dumps(row) for row in data])
    
    print(f"Loading {len(data)} records into BigQuery table '{project_id}.{dataset_id}.{table_id}'...")
    
    load_job = client.load_table_from_file(
        file_obj=io.StringIO(data_as_json_str),
        destination=table_ref,
        job_config=job_config
    )
    
    load_job.result() # Wait for the job to complete
    
    if load_job.errors:
        print(f"Errors encountered during BigQuery load job: {load_job.errors}")
    else:
        print(f"Successfully loaded {load_job.output_rows} rows.")


def main():
    """Main function to fetch data and load it to BigQuery."""
    if not GCP_PROJECT_ID:
        print("Error: Please set the GCP_PROJECT_ID environment variable.")
        return

    # 1. Get the OAuth token from Secret Manager
    print("Fetching Mailchimp token from Secret Manager...")
    token_data = get_secret(GCP_PROJECT_ID, SECRET_ID)
    if not token_data:
        return

    access_token = token_data.get("access_token")
    server_prefix = token_data.get("dc")

    if not access_token or not server_prefix:
        print("Error: 'access_token' or 'dc' (server_prefix) not found in the secret.")
        return

    # 2. Fetch campaigns from Mailchimp API
    print("Fetching campaigns from Mailchimp API...")
    url = f"https://{server_prefix}.api.mailchimp.com/3.0/campaigns"
    headers = {"Authorization": f"OAuth {access_token}"}
    
    # You can adjust params to fetch more data, e.g., by increasing 'count'
    params = {"count": 100, "offset": 0} 
    
    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        print(f"Mailchimp API error: {response.status_code} {response.text}")
        return

    campaigns_data = response.json().get("campaigns", [])
    print(f"Found {len(campaigns_data)} campaigns.")

    if not campaigns_data:
        print("No campaigns to load.")
        return
        
    # 3. Load the data into BigQuery
    load_data_to_bigquery(
        project_id=GCP_PROJECT_ID,
        dataset_id=BIGQUERY_DATASET_ID,
        table_id=BIGQUERY_TABLE_ID,
        data=campaigns_data
    )
    
    print("\n" + "="*80)
    print("Data pipeline finished successfully!")
    print("="*80)


if __name__ == "__main__":
    main() 