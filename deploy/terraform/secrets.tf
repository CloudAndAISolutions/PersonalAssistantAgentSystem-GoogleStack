# Secret Manager definitions for OAuth tokens and API Keys
# (The actual value should be uploaded manually or via a script, not stored in source code)
data "google_secret_manager_secret" "oauth_token" {
  secret_id = "agent-oauth-token"
}

data "google_secret_manager_secret" "gemini_api_key" {
  secret_id = "agent-gemini-api-key"
}