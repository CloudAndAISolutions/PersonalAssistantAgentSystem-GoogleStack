# Service Account for Cloud Run
resource "google_service_account" "agent_sa" {
  account_id   = "personal-agent-sa"
  display_name = "Personal Assistant Agent Service Account"
}

# Grant Datastore/Firestore access
resource "google_project_iam_member" "agent_datastore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.agent_sa.email}"
}

# Grant Secret Manager Secret Accessor
resource "google_project_iam_member" "agent_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.agent_sa.email}"
}

# Grant Vertex AI User if needed for models
resource "google_project_iam_member" "agent_vertexai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.agent_sa.email}"
}
