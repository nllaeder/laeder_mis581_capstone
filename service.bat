@echo off
setlocal enabledelayedexpansion

rem ---------------------------------------------------------------------------
rem This Windows Batch script configures the necessary IAM permissions for the
rem data integration service account in your Google Cloud project.
rem
rem It automatically retrieves your currently configured gcloud project ID.
rem
rem Usage:
rem   1. Make sure you have the gcloud CLI installed and authenticated.
rem      (run 'gcloud auth login' and 'gcloud config set project YOUR_PROJECT_ID')
rem   2. Save this script as 'setup_iam_permissions.bat'.
rem   3. Double-click the file or run it from the Command Prompt.
rem ---------------------------------------------------------------------------

echo --- GCP IAM Permission Setup ---
echo.

rem --- Get the current GCP project ID from gcloud config ---
echo Retrieving your GCP Project ID...
for /f "tokens=*" %%i in ('gcloud config get-value project') do set "PROJECT_ID=%%i"

rem --- Check if Project ID was found ---
if not defined PROJECT_ID (
    echo.
    echo ERROR: Could not retrieve Project ID.
    echo Please make sure you are logged in to gcloud and have a project selected.
    echo Run: 'gcloud auth login' and 'gcloud config set project YOUR_PROJECT_ID'
    echo.
    pause
    exit /b 1
)

echo Project ID found: %PROJECT_ID%
echo.

rem --- Define the Service Account email ---
set "SERVICE_ACCOUNT_EMAIL=data-integration-svc@%PROJECT_ID%.iam.gserviceaccount.com"
echo The following service account will be configured:
echo %SERVICE_ACCOUNT_EMAIL%
echo.

rem --- Grant Secret Manager permissions ---
echo Applying IAM role: roles/secretmanager.secretAccessor
gcloud projects add-iam-policy-binding %PROJECT_ID% ^
    --member="serviceAccount:%SERVICE_ACCOUNT_EMAIL%" ^
    --role="roles/secretmanager.secretAccessor" --condition=None

echo.
echo Applying IAM role: roles/secretmanager.secretVersionAdder
gcloud projects add-iam-policy-binding %PROJECT_ID% ^
    --member="serviceAccount:%SERVICE_ACCOUNT_EMAIL%" ^
    --role="roles/secretmanager.secretVersionAdder" --condition=None

rem --- Grant BigQuery permissions ---
echo.
echo Applying IAM role: roles/bigquery.dataEditor
gcloud projects add-iam-policy-binding %PROJECT_ID% ^
    --member="serviceAccount:%SERVICE_ACCOUNT_EMAIL%" ^
    --role="roles/bigquery.dataEditor" --condition=None

echo.
echo ----------------------------------------
echo IAM policies have been applied successfully.
echo ----------------------------------------
echo.

pause
