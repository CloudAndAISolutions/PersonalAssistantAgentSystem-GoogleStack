# Secret Manager definitions for OAuth tokens and API Keys

resource "google_secret_manager_secret" "oauth_token" {
  secret_id = "agent-oauth-token"
  replication {
    auto {}
  }
}

# (The actual value should be uploaded manually or via a script, not stored in source code)

resource "google_secret_manager_secret" "gemini_api_key" {
  secret_id = "agent-gemini-api-key"
  replication {
    auto {}
  }
}
