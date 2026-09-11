# Walkthrough: Phase 4 (Cloud Deployment)

I've set up the foundational cloud deployment files needed to move the agent system to production on Google Cloud. 

Here is what was accomplished:

## 1. Containerization
- **[`Dockerfile`]**: Added a production-ready Dockerfile configured to run the FastAPI app via `uvicorn`.
- **[`.dockerignore`]**: Ensures local states, credentials, and virtual environments aren't pushed to the container registry.

## 2. Production State Backend (Firestore)
- **[`src/services/config.py`]**: Added support for `USE_FIRESTORE=true`.
- **[`pyproject.toml`]**: Added `google-cloud-firestore`.
- **[`src/services/state.py`]**: Refactored the state manager into a dual-backend system. It automatically routes to `FirestoreBackend` for production or `SQLiteBackend` for local development based on your configuration.

## 3. Terraform Infrastructure
All Terraform files are neatly organised under `deploy/terraform/`:
- **[`main.tf`]**: Provider and project variables.
- **[`iam.tf`]**: Provisions a dedicated Service Account (`personal-agent-sa`) with permissions to access Secrets and Firestore.
- **[`secrets.tf`]**: Secret Manager definitions for OAuth tokens and the Gemini API key.
- **[`cloud_run.tf`]**: The Cloud Run service definition with secret references.
- **[`firestore.tf`]**: Native Firestore database provisioning.
- **[`scheduler.tf`]**: Sets up 4 independent cron jobs pointing to the Cloud Run service endpoints for the morning, evening, and weekly agent routines.

> [!TIP]
> The infrastructure is defined but **not applied**. When you are ready to deploy, you can manually authenticate with `gcloud` and run `terraform apply` in the `deploy/terraform/` directory.
