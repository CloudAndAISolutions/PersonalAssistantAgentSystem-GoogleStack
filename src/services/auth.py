import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# Scopes needed for the agent system
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',       # To read/send emails
    'https://www.googleapis.com/auth/calendar.readonly',  # To read calendar events
    'https://www.googleapis.com/auth/tasks.readonly',     # To read tasks
    'https://www.googleapis.com/auth/documents',          # To create/edit docs
    'https://www.googleapis.com/auth/blogger',            # To create blogger posts
    'https://www.googleapis.com/auth/drive'               # To create files in Drive/Docs
]

def get_credentials():
    """Gets valid user credentials from storage.
    
    In local dev: loads from credentials/token.json
    In production: could be adapted to load from Secret Manager
    """
    creds = None
    token_path = 'credentials/token.json'
    
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Save the refreshed credentials back to the file
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        else:
            raise Exception(f"Valid credentials not found. Please run scripts/setup_oauth.py first.")
            
    return creds
