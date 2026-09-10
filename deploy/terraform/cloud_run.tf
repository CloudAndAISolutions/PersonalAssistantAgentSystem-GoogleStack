resource "google_cloud_run_v2_service" "agent_service" {
  name     = "personal-assistant-agent"
  location = var.region

  template {
    service_account = google_service_account.agent_sa.email
    containers {
      image = var.image_tag

      env {
        name  = "USE_FIRESTORE"
        value = "true"
      }
      env {
        name  = "FIRESTORE_PROJECT_ID"
        value = var.project_id
      }
      # The credentials will be loaded by the application using Google Cloud Secret Manager integration
      # We could pass them directly if we use Cloud Run Secret references:
      env {
        name = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.gemini_api_key.secret_id
            version = "latest"
          }
        }
      }
      
      # Additional non-secret variables (Update these for your environment)
      env {
        name  = "BLOG_BACKEND"
        value = "docs" # or blogger
      }
      env {
        name  = "GOOGLE_DOCS_OUTPUT_FOLDER_ID"
        value = "placeholder-folder-id"
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}
