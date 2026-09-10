from googleapiclient.discovery import build
from src.services.auth import get_credentials
from src.services.config import config


class BloggerTool:
    """Blogger API tool for production blog post drafting.
    
    All posts are created as DRAFTS and never auto-published,
    so you can review and publish manually from Blogger.
    """

    def __init__(self):
        self.creds = get_credentials()
        self.service = build('blogger', 'v3', credentials=self.creds)
        self.blog_id = config.BLOGGER_BLOG_ID

    def create_draft_post(self, title: str, html_content: str, labels: list = None):
        """Creates a new Blogger post as a DRAFT (never published automatically).
        
        Args:
            title: The title of the blog post.
            html_content: HTML body of the blog post.
            labels: Optional list of string labels/tags to attach to the post.
            
        Returns:
            dict with status, post id, and draft URL on success; error message on failure.
        """
        if not self.blog_id:
            return {'status': 'error', 'message': 'BLOGGER_BLOG_ID not configured in .env'}

        body = {
            'title': title,
            'content': html_content,
        }
        if labels:
            body['labels'] = labels

        try:
            # isDraft=True ensures the post is never auto-published
            post = self.service.posts().insert(
                blogId=self.blog_id,
                body=body,
                isDraft=True
            ).execute()

            return {
                'status': 'success',
                'id': post.get('id'),
                'url': post.get('url'),
                'selfLink': post.get('selfLink'),
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def embed_photo_in_post(self, photo_url: str, alt_text: str = 'Photo', width: int = 800):
        """Generates an HTML <img> tag for embedding a photo in a post.
        
        Args:
            photo_url: Direct URL to the photo.
            alt_text: Alt-text description for accessibility.
            width: Display width in pixels (default 800px, height auto).
            
        Returns:
            HTML string containing the img element.
        """
        return f'<figure><img src="{photo_url}" alt="{alt_text}" width="{width}" style="max-width:100%;height:auto;" /><figcaption>{alt_text}</figcaption></figure>'

    def list_draft_posts(self):
        """Lists all draft posts in the configured blog (for inspection/cleanup)."""
        if not self.blog_id:
            return []
        try:
            result = self.service.posts().list(
                blogId=self.blog_id,
                status='DRAFT',
                fields='items(id,title,published,url)'
            ).execute()
            return result.get('items', [])
        except Exception as e:
            return []
