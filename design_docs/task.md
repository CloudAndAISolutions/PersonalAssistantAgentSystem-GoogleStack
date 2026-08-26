# Phase 1: Foundation — Local Dev with Gemini API

- [x] Project Setup
  - [x] Initialize Python virtual environment
  - [x] Create `pyproject.toml` with dependencies (`google-adk`, `google-genai`, `google-api-python-client`, `google-auth-httplib2`, `google-auth-oauthlib`, `fastapi`, `python-dotenv`)
  - [x] Create directory structure (`src/`, `src/agents/`, `src/tools/`, `src/services/`, `scripts/`, `credentials/`, `data/`)
  - [x] Create `.env.example`
- [x] Configure Environment
  - [x] Add `GEMINI_API_KEY` to `.env.example` and set up `config.py` in `src/services/`
- [x] Authentication
  - [x] Create `scripts/setup_oauth.py` for Google Workspace OAuth flow
  - [x] Create `src/services/auth.py` for token management (loading/refreshing `token.json`)
- [x] Core Google API Tools
  - [x] Create `src/tools/gmail_tool.py` (filtered email reading, sending)
  - [x] Create `src/tools/calendar_tool.py` (fetching events)
  - [x] Create `src/tools/tasks_tool.py` (fetching pending/overdue tasks)
  - [x] Create `src/tools/docs_tool.py` (creating drafts)
- [x] Testing
  - [x] Test tools locally using ADK CLI (`adk web` or simple scripts)
