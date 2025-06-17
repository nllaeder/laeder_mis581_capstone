# **App Specification: Marketing Data Connector**

## **1\. Overview**

This document specifies the requirements for a Flask web application designed to connect to marketing platforms (Mailchimp, Constant Contact), download marketing data, and store it in Google BigQuery. The application will be deployed on Google Cloud and will use Google Cloud services for authentication, secret management, and data warehousing.

## **2\. Core Functionality**

### **2.1. User Authentication**

* **Google Sign-In:** Users must authenticate with their Google account (OAuth 2.0).  
* **Session Management:** The application must maintain user sessions to keep users logged in.

### **2.2. Service Integration (OAuth 2.0)**

* **Connect to Marketing Platforms:** Users will be able to initiate an OAuth 2.0 flow to connect their Mailchimp or Constant Contact accounts.  
* **Authorization and Consent:** The application must guide the user through the respective platform's authorization and consent screen.  
* **Token Storage:** Upon successful authorization, the application must securely store the OAuth tokens (access token, refresh token).

### **2.3. Secret Management**

* **Google Cloud Secret Manager:** All sensitive information, particularly the OAuth tokens from Mailchimp and Constant Contact, must be stored in Google Cloud Secret Manager.  
* **Secret Naming Convention:** Secrets should be named in a structured way, linking them to the user ID and the connected service (e.g., user-\[user\_id\]-mailchimp-tokens).

### **2.4. Data Extraction and Loading**

* **API Clients:** The application will include modules to interact with the Mailchimp and Constant Contact APIs.  
* **Data Extraction:** Once a user has connected a service, the application will perform an initial bulk download of all historical marketing data. This includes, but is not limited to:  
  * Lists/Audiences  
  * Campaigns (and their performance metrics)  
  * Contacts/Subscribers  
  * Automations  
* **Data Loading:** The extracted data will be loaded into Google BigQuery.  
* **BigQuery Schema:** A well-defined schema must be created in BigQuery for each data type (e.g., a table for campaigns, a table for contacts).  
* **Incremental Updates:** The application should be designed to handle periodic, incremental updates to fetch new data without re-downloading the entire history.

## **3\. Technical Stack & Architecture**

* **Language:** Python 3.x  
* **Framework:** Flask  
* **Cloud Platform:** Google Cloud  
* **Key Google Cloud Services:**  
  * **Google App Engine (or Cloud Run):** For hosting the Flask application.  
  * **Google Identity Services:** For user authentication.  
  * **Google Cloud Secret Manager:** For storing secrets.  
  * **Google BigQuery:** For data warehousing.  
* **Architecture:**  
  * **Frontend:** Simple HTML/CSS/JavaScript for the user interface. Will be served by Flask templates.  
  * **Backend (Flask):**  
    * /auth: Routes for Google sign-in and sign-out.  
    * /connect: Routes to initiate OAuth flows for marketing platforms.  
    * /callback: Routes to handle the OAuth callback from marketing platforms.  
    * /data: API endpoints to trigger data extraction and loading.  
  * **Task Queue (Optional but Recommended):** For long-running data extraction jobs, consider using Google Cloud Tasks to run them asynchronously.

## **4\. User Interface (UI) Flow**

1. **Login Page:** A simple page with a "Sign in with Google" button.  
2. **Dashboard:** After logging in, the user sees a dashboard.  
   * It displays their login status.  
   * It shows a list of available marketing platforms (Mailchimp, Constant Contact).  
   * For each platform, it shows a "Connect" button or a "Connected" status.  
3. **Connection Flow:**  
   * User clicks "Connect."  
   * User is redirected to the marketing platform's OAuth consent screen.  
   * User approves the connection.  
   * User is redirected back to the application's dashboard.  
4. **Data Sync:**  
   * Once connected, a "Sync Data" button appears.  
   * User clicks "Sync Data" to initiate the data download to BigQuery.  
   * The UI should provide feedback on the status of the sync (e.g., "In Progress," "Completed," "Failed").