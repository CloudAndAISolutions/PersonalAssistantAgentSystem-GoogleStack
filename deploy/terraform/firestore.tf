# Enable Firestore in Datastore mode or Native mode
resource "google_firestore_database" "agent_db" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
}
