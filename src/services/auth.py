import os
import json
import tempfile
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

_LOCAL_TOKEN_PATH = 'credentials/token.json'


def _load_creds_from_env() -> Credentials | None:
    """Load credentials from the GOOGLE_OAUTH_TOKEN_JSON environment variable.

    Cloud Run injects this from Secret Manager at startup.
    The value is the full JSON content of token.json.
    """
    token_json = os.environ.get('GOOGLE_OAUTH_TOKEN_JSON')
    if not token_json:
        return None
    return Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)


def _load_creds_from_file() -> Credentials | None:
    """Load credentials from the local token.json file (dev only)."""
    if os.path.exists(_LOCAL_TOKEN_PATH):
        return Credentials.from_authorized_user_file(_LOCAL_TOKEN_PATH, SCOPES)
    return None


def get_credentials() -> Credentials:
    """Returns valid Google OAuth credentials.

    Resolution order:
      1. GOOGLE_OAUTH_TOKEN_JSON env var  — used in production (Cloud Run)
         The value is injected from Secret Manager by Terraform's cloud_run.tf.
      2. credentials/token.json file       — used in local development

    If the token is expired but has a refresh_token, it is refreshed automatically.
    In production the refreshed token is only held in memory (the secret is not updated).
    In dev the refreshed token is written back to disk.
    """
    # 1. Production: token comes from Secret Manager via env var
    is_production = bool(os.environ.get('GOOGLE_OAUTH_TOKEN_JSON'))
    creds = _load_creds_from_env() or _load_creds_from_file()

    if not creds:
        raise RuntimeError(
            "No OAuth credentials found.\n"
            "  Production: ensure the 'agent-oauth-token' Secret Manager secret is populated\n"
            "              and the GOOGLE_OAUTH_TOKEN_JSON env var is set on Cloud Run.\n"
            "  Local dev:  run `python scripts/setup_oauth.py` to create credentials/token.json."
        )

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            if not is_production:
                # Write refreshed creds back to disk for local dev convenience
                os.makedirs(os.path.dirname(_LOCAL_TOKEN_PATH), exist_ok=True)
                with open(_LOCAL_TOKEN_PATH, 'w') as f:
                    f.write(creds.to_json())
            # In production, refreshed creds live in memory only for this request.
            # The Secret Manager value remains unchanged (update manually when needed).
        else:
            raise RuntimeError(
                "OAuth token is invalid and cannot be refreshed. "
                "Please re-run setup_oauth.py and update the Secret Manager secret."
            )

    return creds
