terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
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
  default     = "us-central1"
}

# The Docker image to deploy
variable "image_tag" {
  type        = string
  description = "The Container Registry or Artifact Registry image URI for the application"
}
