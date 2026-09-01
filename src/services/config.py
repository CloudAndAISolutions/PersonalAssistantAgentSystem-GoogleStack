import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration loaded from environment variables."""
    
    # Model Selection
    # Primary model — used first on every run.
    # If the primary returns a 503 (high demand), the runner falls back to fallback_model_name.
    model_name          = "gemini-3.5-flash"
    fallback_model_name = "gemini-2.5-flash"
    
    # AI Backend Strategy
    USE_VERTEXAI = os.getenv('GOOGLE_GENAI_USE_VERTEXAI', 'false').lower() == 'true'
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    VERTEX_PROJECT_ID = os.getenv('VERTEX_PROJECT_ID')
    VERTEX_LOCATION = os.getenv('VERTEX_LOCATION', 'us-central1')
    
    # Blog Backend
    BLOG_BACKEND = os.getenv('BLOG_BACKEND', 'docs').lower()
    GOOGLE_DOCS_OUTPUT_FOLDER_ID = os.getenv('GOOGLE_DOCS_OUTPUT_FOLDER_ID')
    BLOGGER_BLOG_ID = os.getenv('BLOGGER_BLOG_ID')
    
    # Application Settings
    _skip_senders_raw = os.getenv('EMAIL_SKIP_SENDERS', '')
    EMAIL_SKIP_SENDERS = [s.strip() for s in _skip_senders_raw.split(',')] if _skip_senders_raw else []

    # Partner calendar filtering
    # Set PARTNER_CALENDAR_ID in .env to the partner's Google calendar ID (e.g. their Gmail address)
    # Events from that calendar whose titles match any PARTNER_EXCLUDE_CATEGORIES keyword are hidden.
    PARTNER_CALENDAR_ID = os.getenv('PARTNER_CALENDAR_ID')  # no default — must be set in .env
    _partner_exclude_raw = os.getenv(
        'PARTNER_EXCLUDE_CATEGORIES',
        'fitness,wellness,gym,yoga,pilates,crossfit,class,training,workout,exercise,heated,strength,cycling,spin,barre,dance,meditation,stretch,bootcamp,hiit,run,walk'
    )
    PARTNER_EXCLUDE_CATEGORIES = [s.strip().lower() for s in _partner_exclude_raw.split(',')]
    
    LOCAL_DB_PATH = os.getenv('LOCAL_DB_PATH', 'data/agent_state.db')
    
    @classmethod
    def validate(cls):
        """Validates that required configuration is present."""
        if cls.USE_VERTEXAI:
            if not cls.VERTEX_PROJECT_ID:
                raise ValueError("VERTEX_PROJECT_ID must be set when GOOGLE_GENAI_USE_VERTEXAI is true")
        else:
            if not cls.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY must be set when GOOGLE_GENAI_USE_VERTEXAI is false")
                
        if cls.BLOG_BACKEND == 'docs' and not cls.GOOGLE_DOCS_OUTPUT_FOLDER_ID:
            print("WARNING: GOOGLE_DOCS_OUTPUT_FOLDER_ID not set. Documents will be created in the root directory.")
            
        if cls.BLOG_BACKEND == 'blogger' and not cls.BLOGGER_BLOG_ID:
            raise ValueError("BLOGGER_BLOG_ID must be set when BLOG_BACKEND is 'blogger'")

config = Config()
