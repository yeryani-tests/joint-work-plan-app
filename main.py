import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from datetime import datetime
import os

# --- Page Configuration ---
st.set_page_config(
    page_title="Joint Work Plan (JWP) Tracker",
    page_icon="🇺🇳",
    layout="wide",
)

# --- Google Sheets Configuration ---
def get_gspread_client():
    """
    Initializes and returns a gspread client object.
    Uses Streamlit secrets to securely store Google Service Account credentials.
    """
    try:
        # Check if running on Streamlit Cloud
        if 'GSPREAD_CREDENTIALS' in st.secrets:
            creds_json = st.secrets["GSPREAD_CREDENTIALS"]
        # Check if running locally with env var
        elif 'GSPREAD_CREDENTIALS' in os.environ:
            creds_json = os.environ.get("GSPREAD_CREDENTIALS")
        else:
            st.error("Google Sheets credentials not found. Please set them in Streamlit secrets or environment variables.")
            st.stop()
            
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(creds_json), scope)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Failed to connect to Google Sheets: {e}")
        st.info("Please ensure your Google Service Account credentials are correctly configured in Streamlit secrets.")
        st.stop()

def get_data_from_gsheet(client, sheet_name="JWP_Data", worksheet_name="Sheet1"):
    """
    Fetches data from a Google Sheet and returns it as a Pandas DataFrame.
    """
    try:
        sheet = client.open(sheet_name).worksheet(worksheet_name)
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Spreadsheet '{sheet_name}' not found. Please create it or check the name.")
        return pd.DataFrame()
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"Worksheet '{worksheet_name}' not found in '{sheet_name}'.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"An error occurred while fetching data: {e}")
        return pd.DataFrame()

def update_gsheet_from_dataframe(client, df, sheet_name="JWP_Data", worksheet_name="Sheet1"):
    """
    Updates a Google Sheet with data from a Pandas DataFrame.
    """
    try:
        sheet = client.open(sheet_name).worksheet(worksheet_name)
        sheet.clear()
        # Convert DataFrame to a list of lists to upload
        sheet.update([df.columns.values.tolist()] + df.values.tolist())
        return True
    except Exception as e:
        st.error(f"Failed to update Google Sheet: {e}")
        return False
        
def log_edit(client, user_name, user_email, agency, activity, changes):
    """Logs an edit to the audit log in Google Sheets."""
    try:
        log_sheet = client.open("JWP_Data").worksheet("Audit_Log")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = [timestamp, user_name, user_email, agency, activity, json.dumps(changes)]
        log_sheet.append_row(log_entry)
    except gspread.exceptions.WorksheetNotFound:
        # Create the sheet if it doesn't exist
        sh = client.open("JWP_Data")
        log_sheet = sh.add_worksheet(title="Audit_Log", rows="1000", cols="6")
        log_sheet.append_row(["Timestamp", "User Name", "User Email", "Agency", "Activity", "Changes"])
        log_entry = [timestamp, user_name, user_email, agency, activity, json.dumps(changes)]
        log_sheet.append_row(log_entry)
    except Exception as e:
        st.warning(f"Could not write to audit log: {e}")

# --- Main Application Logic ---
def main():
    st.title("Joint Work Plan (JWP) Progress Tracker")
    st.markdown("---")

    # --- Session State Initialization ---
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        st.session_state['user_name'] = ""
        st.session_state['user_email'] = ""
        st.session_state['user_agency'] = ""
        st.session_state['is_admin'] = False

    # Initialize client and data
    client = get_gspread_client()
    master_df = get_data_from_gsheet(client)

    if master_df.empty:
        st.warning("The master dataset is empty. The admin may need to upload the initial CSV.")
        # Create a placeholder dataframe if empty
        master_df = pd.DataFrame(columns=[
            'Outcome', 'Sub-Output', 'Agency', 'Activity', 
            'End Date', 'Budget Spent', 'Progress / Achievement to Date', 'Last Updated'
        ])

    # --- Login / Main View Logic ---
    if not st.session_state['logged_in']:
        login_view(master_df)
    else:
        if st.session_state['is_admin']:
            admin_view(client, master_df)
        else:
            stakeholder_view(client, master_df)

def login_view(df):
    """Displays the login form for stakeholders and admins."""
    st.header("Login")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        agencies = sorted(df['Agency'].unique().tolist()) if 'Agency' in df.columns else []
        
        user_name = st.text_input("Your Name", key="login_name")
        user_email = st.text_input("Your Email", key="login_email")
        user_agency = st.selectbox("Select Your Agency", agencies, key="login_agency", index=0 if agencies else None)
        
        if st.button("Login as Stakeholder"):
            if user_name and user_email and user_agency:
                st.session_state['logged_in'] = True
                st.session_state['user_name'] = user_name
                st.session_state['user_email'] = user_email
                st.session_state['user_agency'] = user_agency
                st.session_state['is_admin'] = False
                st.rerun()
            else:
                st.error("Please fill in all fields.")
        
        st.markdown("---")
        
        admin_password = st.text_input("Admin Password", type="password", key="admin_pass")
        if st.button("Login as Admin"):
            # Get admin password from secrets
            correct_password = st.secrets.get("ADMIN_PASSWORD", os.environ.get("ADMIN_PASSWORD"))
            if not correct_password:
                st.error("Admin password is not configured on the server.")
            elif admin_password == correct_password:
                st.session_state['logged_in'] = True
                st.session_state['user_name'] = "Admin"
                st.session_state['user_email'] = "admin@system"
                st.session_state['user_agency'] = "All"
                st.session_state['is_admin'] = True
                st.rerun()
            else:
                st.error("Incorrect admin password.")
                
    with col2:
        st.info(
            """
            **Welcome to the JWP Tracker**

            - **Stakeholders:** Please enter your name, email, and select your agency to log in. You will be able to view and edit the activities assigned to your agency.
            - **Admins:** Enter the admin password to access the full dataset, download reports, and view the audit log.
            """
        )

def stakeholder_view(client, master_df):
    """Displays the data editor for a logged-in stakeholder."""
    st.sidebar.header(f"Welcome, {st.session_state['user_name']}")
    st.sidebar.write(f"**Agency:** {st.session_state['user_agency']}")
    if st.sidebar.button("Logout"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()
    
    st.header(f"Activities for {st.session_state['user_agency']}")
    st.info("You can edit the 'End Date', 'Budget Spent', and 'Progress' columns for your agency's activities. The first four columns are locked. Click 'Save Updates' below the table to persist your changes.")
    
    # Filter data for the user's agency
    agency_df = master_df[master_df['Agency'] == st.session_state['user_agency']].copy()
    
    if agency_df.empty:
        st.warning("No activities found for your agency.")
        return

    # Use st.data_editor for interactive editing
    edited_df = st.data_editor(
        agency_df,
        key="data_editor",
        disabled=['Outcome', 'Sub-Output', 'Agency', 'Activity', 'Last Updated'],
        column_config={
            "End Date": st.column_config.DateColumn(
                "End Date",
                format="YYYY-MM-DD",
                help="Target completion date for the activity."
            ),
            "Budget Spent": st.column_config.NumberColumn(
                "Budget Spent (USD)",
                help="Total budget spent on this activity to date.",
                format="$ %d",
            ),
        },
        use_container_width=True,
        hide_index=True
    )
    
    if st.button("Save Updates"):
        # Detect changes
        changes = []
        if not edited_df.equals(agency_df):
            # Create a comparison dataframe to find what changed
            diff_mask = (edited_df != agency_df).any(axis=1)
            changed_rows = edited_df[diff_mask]

            for index, row in changed_rows.iterrows():
                original_row = master_df.loc[index]
                activity_identifier = original_row['Activity']
                change_details = {}
                
                # Check each editable column for changes
                for col in ['End Date', 'Budget Spent', 'Progress / Achievement to Date']:
                    if str(row[col]) != str(original_row[col]):
                        change_details[col] = f"from '{original_row[col]}' to '{row[col]}'"
                
                if change_details:
                    # Log the edit
                    log_edit(
                        client,
                        st.session_state['user_name'],
                        st.session_state['user_email'],
                        st.session_state['user_agency'],
                        activity_identifier,
                        change_details
                    )
                    
                    # Update master dataframe in memory
                    master_df.loc[index, 'Last Updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    for col, val in row.items():
                         master_df.loc[index, col] = val

            # Update the Google Sheet
            if update_gsheet_from_dataframe(client, master_df):
                st.success("Your updates have been saved successfully!")
                st.rerun() # Rerun to show the latest data
            else:
                st.error("Failed to save updates. Please try again.")
        else:
            st.info("No changes were detected.")

def admin_view(client, master_df):
    """Displays the admin panel for viewing all data, downloading, and viewing logs."""
    st.sidebar.header("Admin Panel")
    if st.sidebar.button("Logout"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

    st.header("Master Data View")
    st.info("As an admin, you can view all data, upload a new master CSV, and download the latest data.")
    
    st.dataframe(master_df, use_container_width=True)
    
    # --- CSV Download ---
    @st.cache_data
    def convert_df_to_csv(df):
        return df.to_csv(index=False).encode('utf-8')

    csv_data = convert_df_to_csv(master_df)
    st.download_button(
        label="📥 Download Full Updated CSV",
        data=csv_data,
        file_name="JWP_master_data_updated.csv",
        mime="text/csv",
    )
    
    st.markdown("---")
    
    # --- Audit Log Viewer ---
    st.header("Audit Log of Edits")
    try:
        log_df = get_data_from_gsheet(client, worksheet_name="Audit_Log")
        if not log_df.empty:
            st.dataframe(log_df.sort_values(by="Timestamp", ascending=False), use_container_width=True)
        else:
            st.info("The audit log is currently empty.")
    except Exception as e:
        st.error(f"Could not load audit log: {e}")
        
    st.markdown("---")
    
    # --- Initial Data Upload ---
    st.header("Initial Data Setup")
    st.warning("Use this section only for the initial setup or to completely overwrite the existing data.")
    uploaded_file = st.file_uploader("Upload a CSV file to initialize or overwrite the master dataset", type="csv")
    
    if uploaded_file is not None:
        try:
            new_df = pd.read_csv(uploaded_file)
            # Basic validation
            expected_cols = ['Outcome', 'Sub-Output', 'Agency', 'Activity']
            if all(col in new_df.columns for col in expected_cols):
                # Add required columns if they don't exist
                if 'End Date' not in new_df.columns: new_df['End Date'] = None
                if 'Budget Spent' not in new_df.columns: new_df['Budget Spent'] = 0
                if 'Progress / Achievement to Date' not in new_df.columns: new_df['Progress / Achievement to Date'] = ''
                if 'Last Updated' not in new_df.columns: new_df['Last Updated'] = None
                
                if st.button("Confirm Overwrite"):
                    if update_gsheet_from_dataframe(client, new_df):
                        st.success("Successfully overwrote the master data.")
                        st.rerun()
                    else:
                        st.error("Failed to overwrite data.")
            else:
                st.error(f"The uploaded CSV is missing one of the required columns: {expected_cols}")
        except Exception as e:
            st.error(f"An error occurred while processing the file: {e}")


if __name__ == "__main__":
    main()
