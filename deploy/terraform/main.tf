terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # Remote state stored in a GCS bucket — prevents drift between CI runs.
  # Create the bucket ONCE manually:
  #   gcloud storage buckets create gs://<YOUR_PROJECT_ID>-tfstate --location=us-central1
  backend "gcs" {
    bucket = "storied-program-359407-tfstate" # ← set to <your-project-id>-tfstate
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  type        = string
  description = "The GCP project ID"
}

variable "region" {
  type        = string
  description = "The GCP region for resources (e.g., us-central1)"
  default     = "australia-southeast1"
}

# The Docker image to deploy (passed in by CI as the newly-built digest)
variable "image_tag" {
  type        = string
  description = "Full Artifact Registry image URI including digest or tag"
}

variable "blog_backend" {
  type        = string
  description = "Blog backend: 'docs' or 'blogger'"
  default     = "docs"
}

variable "google_docs_folder_id" {
  type        = string
  description = "Google Drive folder ID for Docs output"
  default     = ""
}

variable "blogger_blog_id" {
  type        = string
  description = "Blogger blog ID (only required when blog_backend = blogger)"
  default     = ""
}

variable "partner_calendar_id" {
  type        = string
  description = "Partner's Google Calendar ID for fitness event filtering"
  default     = ""
}

variable "partner_exclude_categories" {
  type        = string
  description = "Comma-separated keywords to filter from the partner's calendar (e.g. fitness event titles)"
  default     = "fitness,wellness,gym,yoga,pilates,crossfit,class,training,workout,exercise,heated,strength,cycling,spin,barre,dance,meditation,stretch,bootcamp,hiit,run,walk"
}
