from googleapiclient.discovery import build
from src.services.auth import get_credentials
from src.services.config import config
import base64
from email.message import EmailMessage

class GmailTool:
    def __init__(self):
        self.creds = get_credentials()
        self.service = build('gmail', 'v1', credentials=self.creds)
        self.user_id = 'me'

    def _get_noise_filter(self) -> str:
        """Returns the Gmail query string to filter out noise."""
        query = (
            "-category:promotions "
            "-category:social "
            "-category:updates "
            "-category:forums "
            "-{unsubscribe} "
            "-from:noreply@* "
            "-from:newsletter@* "
            "-from:marketing@* "
            "-from:digest@* "
        )
        if config.EMAIL_SKIP_SENDERS:
            skip_senders = " ".join([f"-from:{sender}" for sender in config.EMAIL_SKIP_SENDERS])
            query += f" {skip_senders}"
        return query

    def get_unread_emails(self, max_results=10, since="1d"):
        """Fetches unread personal/work emails, filtering out noise."""
        noise_filter = self._get_noise_filter()
        query = f"is:unread newer_than:{since} {noise_filter}"
        
        results = self.service.users().messages().list(userId=self.user_id, q=query, maxResults=max_results).execute()
        messages = results.get('messages', [])
        
        emails = []
        for msg in messages:
            msg_data = self.service.users().messages().get(userId=self.user_id, id=msg['id'], format='metadata', metadataHeaders=['From', 'Subject', 'Date']).execute()
            headers = msg_data.get('payload', {}).get('headers', [])
            
            email_info = {
                'id': msg['id'],
                'snippet': msg_data.get('snippet', ''),
                'from': next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown'),
                'subject': next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject'),
                'date': next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
            }
            emails.append(email_info)
            
        return emails

    def get_important_emails(self, max_results=10, since="1d"):
        """Fetches starred or important emails."""
        query = f"(is:starred OR is:important) newer_than:{since}"
        
        results = self.service.users().messages().list(userId=self.user_id, q=query, maxResults=max_results).execute()
        messages = results.get('messages', [])
        
        emails = []
        for msg in messages:
            msg_data = self.service.users().messages().get(userId=self.user_id, id=msg['id'], format='metadata', metadataHeaders=['From', 'Subject', 'Date']).execute()
            headers = msg_data.get('payload', {}).get('headers', [])
            
            email_info = {
                'id': msg['id'],
                'snippet': msg_data.get('snippet', ''),
                'from': next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown'),
                'subject': next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject'),
                'date': next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
            }
            emails.append(email_info)
            
        return emails

    def send_email(self, to: str, subject: str, html_body: str):
        """Sends an HTML email."""
        if to == 'me':
            try:
                profile = self.service.users().getProfile(userId=self.user_id).execute()
                to = profile.get('emailAddress', 'me')
            except Exception:
                pass
                
        message = EmailMessage()
        message.set_content(html_body, subtype='html')
        message['To'] = to
        message['From'] = 'me'
        message['Subject'] = subject

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': encoded_message}

        send_message = (self.service.users().messages().send(userId=self.user_id, body=create_message).execute())
        return send_message

    def search_emails(self, query: str, max_results=10):
        """Searches emails by Gmail query syntax (e.g. 'from:boss@company.com subject:Q2')."""
        results = self.service.users().messages().list(
            userId=self.user_id, q=query, maxResults=max_results
        ).execute()
        messages = results.get('messages', [])

        emails = []
        for msg in messages:
            msg_data = self.service.users().messages().get(
                userId=self.user_id, id=msg['id'],
                format='metadata', metadataHeaders=['From', 'Subject', 'Date']
            ).execute()
            headers = msg_data.get('payload', {}).get('headers', [])
            emails.append({
                'id': msg['id'],
                'snippet': msg_data.get('snippet', ''),
                'from': next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown'),
                'subject': next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject'),
                'date': next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
            })
        return emails

