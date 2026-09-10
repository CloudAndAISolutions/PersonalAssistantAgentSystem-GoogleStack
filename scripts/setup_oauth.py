import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Scopes needed for the agent system
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',       # To read/send emails
    'https://www.googleapis.com/auth/calendar.readonly',  # To read calendar events
    'https://www.googleapis.com/auth/tasks.readonly',     # To read tasks
    'https://www.googleapis.com/auth/documents',          # To create/edit docs
    'https://www.googleapis.com/auth/blogger',            # To create blogger posts
    'https://www.googleapis.com/auth/drive'               # To create files in Drive/Docs
]

def main():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    
    # Check if credentials folder exists
    os.makedirs('credentials', exist_ok=True)
    
    token_path = 'credentials/token.json'
    client_secrets_path = 'credentials/client_secrets.json'

    if not os.path.exists(client_secrets_path):
        print(f"Error: Could not find {client_secrets_path}")
        print("Please download your OAuth client ID JSON from Google Cloud Console")
        print("and save it as 'credentials/client_secrets.json'")
        return

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired token...")
            creds.refresh(Request())
        else:
            print("Initiating OAuth flow. Please check your browser to log in.")
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secrets_path, SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
            print(f"Token saved to {token_path}")

    print("Authentication successful!")

if __name__ == '__main__':
    main()
