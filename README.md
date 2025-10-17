Joint Work Plan (JWP) Progress Tracker

This Streamlit web application provides a collaborative platform for stakeholders to update their progress on a Joint Work Plan. It features a simple login system, role-based permissions (stakeholder vs. admin), and persistent data storage using Google Sheets as a backend.

Features

Stakeholder Login: Simple login using Name, Email, and Agency. No password required.

Filtered Views: Stakeholders only see and edit activities relevant to their agency.

Read-Only & Editable Columns: The first four columns (Outcome, Sub-Output, Agency, Activity) are locked, while the last three (End Date, Budget Spent, Progress) are editable.

Persistent Storage: All updates are saved to a central Google Sheet, acting as the master dataset.

Admin Panel: A password-protected section for administrators.

Full Data Download: Admins can view and download the complete, up-to-date dataset as a CSV file.

Audit Log: Admins can view a log of all edits, including who made the change, when, and what was changed.

Initial Data Upload: Admins can upload a CSV to initialize or overwrite the master data.

Local Setup and Execution

Prerequisites

Python 3.8+

pip (Python package installer)

Installation

Clone the repository:

git clone <your-repo-url>
cd <your-repo-directory>


Install dependencies:

pip install -r requirements.txt


Configure Credentials (for local run):

To run the app locally, you need to set up Google Service Account credentials and the admin password as environment variables.

Create a file named .env in the root directory and add the following:

# .env file
ADMIN_PASSWORD="your_strong_admin_password"
GSPREAD_CREDENTIALS='{"type": "service_account", "project_id": "...", ...}'


You will need to load these environment variables into your shell before running the app. Alternatively, the app code is configured to read these directly if you use a library like python-dotenv (not included by default). For simplicity, you can also set them directly in your terminal:

export ADMIN_PASSWORD="your_strong_admin_password"
export GSPREAD_CREDENTIALS='...' # Paste the full JSON content here


Running the App

Execute the following command in your terminal:

streamlit run app.py


The application should open in your default web browser.

Deployment to Streamlit Cloud

1. Prepare Your Files

Ensure your GitHub repository has the following file structure:

/
|-- app.py
|-- requirements.txt
|-- jwp_data.csv (optional, for initial setup)
|-- README.md


2. Push to GitHub

Commit your files and push them to a new GitHub repository.

3. Deploy on Streamlit Cloud

Go to share.streamlit.io and sign in.

Click "New app" and select your repository, branch, and the main file (app.py).

Click "Deploy!".

4. Configure Streamlit Secrets

After deployment, your app will show an error because the secrets are not set.

In your app's dashboard on Streamlit Cloud, click the "Settings" icon (three dots) and go to "Settings".

Navigate to the "Secrets" section.

Add the following secrets:

ADMIN_PASSWORD:

Key: ADMIN_PASSWORD

Value: your_super_secret_admin_password

GSPREAD_CREDENTIALS:

Key: GSPREAD_CREDENTIALS

Value: Paste the entire content of your Google Cloud Service Account JSON key file here. The value should look like this:

# This is an example, use your actual credentials
GSPREAD_CREDENTIALS = '''
{
  "type": "service_account",
  "project_id": "your-gcp-project-id",
  "private_key_id": "your-private-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "your-service-account-email@...gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "[https://accounts.google.com/o/oauth2/auth](https://accounts.google.com/o/oauth2/auth)",
  "token_uri": "[https://oauth2.googleapis.com/token](https://oauth2.googleapis.com/token)",
  "auth_provider_x509_cert_url": "[https://www.googleapis.com/oauth2/v1/certs](https://www.googleapis.com/oauth2/v1/certs)",
  "client_x509_cert_url": "..."
}
'''


Click "Save". Your app will automatically reboot with the new secrets.

How to set up Google Service Account Credentials:

Go to the Google Cloud Console.

Create a new project (or select an existing one).

Enable the Google Sheets API and Google Drive API for your project.

Go to "Credentials", click "Create Credentials", and select "Service account".

Fill in the details and grant it a role (e.g., "Editor" is sufficient).

After creating the service account, go to the "Keys" tab for that account, click "Add Key", and select "JSON". A JSON key file will be downloaded.

IMPORTANT: Open the Google Sheet you want to use as your database. Click the "Share" button and share it with the client_email found inside your downloaded JSON file, giving it "Editor" permissions.

Alternative Storage: Using a Database (SQLite/Postgres)

While this app is built for Google Sheets, you can adapt it to use a database.

Trade-offs

Google Sheets: Easy setup, no database hosting required, familiar interface. Can be slow with large datasets and lacks robust database features (e.g., transactions, granular access control).

SQLite: File-based, great for simple, single-user, or low-concurrency apps. Not ideal for multi-instance deployments like on Streamlit Cloud if you need a persistent, shared database.

PostgreSQL: Robust, scalable, and production-ready. Requires a hosted database service (e.g., Heroku, AWS RDS, Supabase), which may incur costs and adds setup complexity.

Instructions to Switch

Update requirements.txt:

For Postgres, add psycopg2-binary and sqlalchemy.

For SQLite, no new packages are needed if using Python's built-in sqlite3, but sqlalchemy is recommended for easier interaction.

Modify app.py:

Replace the gspread functions (get_gspread_client, get_data_from_gsheet, update_gsheet_from_dataframe) with database connection and query functions.

Use a library like SQLAlchemy to create a connection engine. Store your database connection string in Streamlit secrets.

Rewrite the data fetching logic to execute a SELECT * FROM your_table; query.

Rewrite the data update logic to perform UPDATE your_table SET ... WHERE ...; for each changed row.

# Example of switching to SQLAlchemy (conceptual)

# import sqlalchemy as db

# def get_db_engine():
#     # Store a DB connection string like "postgresql://user:password@host/db" in secrets
#     db_url = st.secrets["DATABASE_URL"]
#     engine = db.create_engine(db_url)
#     return engine

# def get_data_from_db(engine):
#     with engine.connect() as connection:
#         df = pd.read_sql("SELECT * FROM jwp_activities", connection)
#     return df

# def update_db_from_dataframe(engine, changed_row, index):
#     with engine.connect() as connection:
#         # This is simplified; a real implementation would be more robust
#         connection.execute(f"UPDATE jwp_activities SET ... WHERE id = {index}")
