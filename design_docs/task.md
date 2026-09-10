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

# Phase 2: Agents — Multi-Agent Layer with Google ADK

## Tools (src/tools/)
- [x] `gmail_tool.py` — `get_unread_emails`, `get_important_emails`, `send_email`, `search_emails`
- [x] `calendar_tool.py` — `get_today_events`, `get_upcoming_events`, `get_reminders`; partner fitness/wellness filter
- [x] `tasks_tool.py` — `get_pending_tasks`, `get_due_today`, `get_overdue_tasks`
- [x] `docs_tool.py` — `create_blog_doc` (folder auto-resolve), `insert_image_to_doc`, `list_blog_docs`
- [x] `blogger_tool.py` — `create_draft_post`, `embed_photo_in_post`, `list_draft_posts` (draft-only, never auto-publishes)

## Services (src/services/)
- [x] `auth.py` — OAuth token management with full scope list (Gmail, Calendar, Tasks, Docs, Drive, Blogger)
- [x] `config.py` — Primary model `gemini-3.5-flash`, fallback `gemini-2.5-flash`; partner calendar filter config; no PII in source
- [x] `state.py` — SQLite state store: run history, daily digest storage for weekly rollup, deduplication
- [x] `runner_utils.py` — `run_agent_with_fallback()`: auto-retries with fallback model on 503 UNAVAILABLE

## Agents (src/agents/)
- [x] `morning_feed.py` — `compile_and_send_briefing` tool (avoids MALFORMED_FUNCTION_CALL on large HTML payloads)
- [x] `journalist.py` — Summarises day emails + events into factual bullet points; `make_journalist_agent()` factory for multi-parent use
- [x] `writer.py` — Transforms bullet points into narrative HTML daily journal; Doc title includes full human-readable date
- [x] `blogger_writer.py` — Standalone agent; saves daily journal drafts to Blogger (`create_blogger_draft` tool); never auto-publishes
- [x] `coordinator.py` — Orchestrates all flows; 4-trigger routing:
  - Trigger 1 `morning_feed`    → `morning_feed_agent` (email briefing)
  - Trigger 2 `evening_digest`  → `evening_flow` SequentialAgent: journalist → writer (Google Docs)
  - Trigger 3 `weekly_report`   → `weekly_writer_agent` (weekly report → Google Docs only)
  - Trigger 4 `weekly_blogger`  → `weekly_publisher_agent` (weekly report → Google Docs + Blogger draft)
- [x] `weekly_writer_agent` — In `coordinator.py`; saves weekly report to Google Docs only
- [x] `weekly_publisher_agent` — In `coordinator.py`; saves weekly report to both Google Docs AND Blogger draft in one pass; tool: `publish_weekly_report`

## Testing & Quality
- [x] `scripts/test_agents.py` — All 4 triggers testable interactively (Morning, Evening, Weekly, Weekly Blogger)
- [x] End-to-end verified: Morning email ✅ · Evening Google Doc ✅ · Weekly Report Google Doc ✅ · Blogger (requires BLOGGER_BLOG_ID in .env)
- [x] Gemini-3.5-flash → 2.5-flash model fallback on 503 implemented and tested
- [x] Partner calendar (fitness/wellness) exclusion filter implemented and config-driven
- [x] All PII removed from source code; sensitive values moved to `.env`
- [x] Google Doc titles include human-readable date (e.g. "Daily Journal — Tuesday, 2 September 2026")

# Phase 3: Local Integration
- [x] `src/main.py` — FastAPI server with `/trigger/{agent_type}` and `/health` endpoints
- [x] End-to-end local API testing (verified `/health` and `/trigger/morning_feed` trigger execute correctly via HTTP)
