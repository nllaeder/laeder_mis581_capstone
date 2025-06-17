# Marketing Data Connector

This Flask application allows users to connect their marketing platforms (Mailchimp, Constant Contact) and sync data to Google BigQuery.

## Prerequisites

- Python 3.x
- Google Cloud project with OAuth 2.0 credentials
- Client secrets file for Google OAuth

## Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd authorization_service
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Update the `CLIENT_SECRETS_FILE` path in `app/__init__.py` with your Google OAuth client secrets file path.

5. Set the `SECRET_KEY` environment variable (optional, defaults to 'dev_key'):
   ```bash
   export SECRET_KEY='your-secret-key'  # On Windows, use `set SECRET_KEY=your-secret-key`
   ```

## Running the Application

1. Start the Flask development server:
   ```bash
   flask run
   ```

2. Open your web browser and navigate to `http://127.0.0.1:5000/`.

3. Click the "Sign in with Google" button to authenticate.

4. After signing in, you will be redirected to the dashboard.

## Next Steps

- Implement OAuth flows for Mailchimp and Constant Contact.
- Set up Google Cloud Secret Manager for storing OAuth tokens.
- Create API client modules for data extraction and BigQuery integration. 