from googleapiclient.discovery import build
from src.services.auth import get_credentials
from src.services.config import config

class DocsTool:
    def __init__(self):
        self.creds = get_credentials()
        self.drive_service = build('drive', 'v3', credentials=self.creds)

    def create_blog_doc(self, title: str, html_content: str):
        """Creates a Google Doc draft from HTML content.
        
        Uses the Drive API to upload the HTML file and convert it to a Google Doc,
        which is much simpler than using the Docs API batchUpdate with raw JSON.
        """
        # Define the file metadata
        file_metadata = {
            'name': title,
            'mimeType': 'application/vnd.google-apps.document'
        }
        
        if config.GOOGLE_DOCS_OUTPUT_FOLDER_ID:
            file_metadata['parents'] = [config.GOOGLE_DOCS_OUTPUT_FOLDER_ID]
            
        # We need to write the HTML to a temporary file or use MediaIoBaseUpload
        from googleapiclient.http import MediaIoBaseUpload
        import io
        
        # Create a file-like object containing the HTML
        fh = io.BytesIO(html_content.encode('utf-8'))
        
        media = MediaIoBaseUpload(
            fh,
            mimetype='text/html',
            resumable=True
        )
        
        try:
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            ).execute()
            
            return {
                'id': file.get('id'),
                'url': file.get('webViewLink'),
                'status': 'success'
            }
        except Exception as e:
            print(f"Error creating Google Doc: {e}")
            return {'status': 'error', 'message': str(e)}
