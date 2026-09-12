resource "google_cloud_run_v2_service" "agent_service" {
  name     = "personal-assistant-agent"
  location = var.region

  template {
    service_account = google_service_account.agent_sa.email

    # Increase timeout for long-running agent runs (Gemini can take ~30s)
    timeout = "300s"

    containers {
      image = var.image_tag

      # ── Non-secret runtime config ─────────────────────────────────────────
      env {
        name  = "USE_FIRESTORE"
        value = "true"
      }
      env {
        name  = "FIRESTORE_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "BLOG_BACKEND"
        value = var.blog_backend
      }
      env {
        name  = "GOOGLE_DOCS_OUTPUT_FOLDER_ID"
        value = var.google_docs_folder_id
      }
      env {
        name  = "BLOGGER_BLOG_ID"
        value = var.blogger_blog_id
      }
      env {
        name  = "PARTNER_CALENDAR_ID"
        value = var.partner_calendar_id
      }
      env {
        name  = "PARTNER_EXCLUDE_CATEGORIES"
        value = var.partner_exclude_categories
      }

      # ── Secrets from Secret Manager ───────────────────────────────────────
      env {
        name = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = data.google_secret_manager_secret.gemini_api_key.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "GOOGLE_OAUTH_TOKEN_JSON"
        value_source {
          secret_key_ref {
            secret  = data.google_secret_manager_secret.oauth_token.secret_id
            version = "latest"
          }
        }
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}
