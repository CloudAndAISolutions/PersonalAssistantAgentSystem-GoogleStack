from googleapiclient.discovery import build
from src.services.auth import get_credentials
from src.services.config import config

class DocsTool:
    def __init__(self):
        self.creds = get_credentials()
        self.drive_service = build('drive', 'v3', credentials=self.creds)

    def _resolve_folder_id(self, folder_name_or_id: str) -> str:
        """Resolves a folder name or ID to an actual Google Drive folder ID.
        
        If a folder with this name exists, returns its ID.
        If it's already a valid ID, returns it.
        Otherwise, creates a folder with this name and returns the new ID.
        """
        if not folder_name_or_id:
            return None
            
        # 1. Search for folder by name
        query = f"name = '{folder_name_or_id}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        try:
            results = self.drive_service.files().list(
                q=query, 
                spaces='drive', 
                fields='files(id, name)'
            ).execute()
            files = results.get('files', [])
            if files:
                return files[0].get('id')
        except Exception:
            pass
            
        # 2. Check if it's an existing folder ID
        try:
            folder = self.drive_service.files().get(
                fileId=folder_name_or_id, 
                fields='id, mimeType'
            ).execute()
            if folder.get('mimeType') == 'application/vnd.google-apps.folder':
                return folder_name_or_id
        except Exception:
            pass
            
        # 3. Create a new folder with this name
        try:
            file_metadata = {
                'name': folder_name_or_id,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = self.drive_service.files().create(
                body=file_metadata, 
                fields='id'
            ).execute()
            return folder.get('id')
        except Exception as e:
            print(f"Error creating folder '{folder_name_or_id}': {e}")
            return None

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
            folder_id = self._resolve_folder_id(config.GOOGLE_DOCS_OUTPUT_FOLDER_ID)
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
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
