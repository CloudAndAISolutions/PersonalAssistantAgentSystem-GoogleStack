# Shared variables for scheduler jobs
locals {
  service_url = google_cloud_run_v2_service.agent_service.uri
}

# 1. Morning Feed (7 AM Daily)
resource "google_cloud_scheduler_job" "morning_feed" {
  name        = "morning-feed-trigger"
  description = "Triggers the Morning Feed agent"
  schedule    = "0 7 * * *"
  time_zone   = "Australia/Brisbane"

  http_target {
    http_method = "POST"
    uri         = "${local.service_url}/trigger/morning_feed"
    
    oidc_token {
      service_account_email = google_service_account.agent_sa.email
    }
  }
}

# 2. Evening Digest (8 PM Daily)
resource "google_cloud_scheduler_job" "evening_digest" {
  name        = "evening-digest-trigger"
  description = "Triggers the Evening Digest agent (Google Docs)"
  schedule    = "0 20 * * *"
  time_zone   = "Australia/Brisbane"

  http_target {
    http_method = "POST"
    uri         = "${local.service_url}/trigger/evening_digest"
    
    oidc_token {
      service_account_email = google_service_account.agent_sa.email
    }
  }
}

# 3. Weekly Report (Google Docs Only) (8 PM Sunday)
resource "google_cloud_scheduler_job" "weekly_report" {
  name        = "weekly-report-trigger"
  description = "Triggers the Weekly Report agent (Google Docs only)"
  schedule    = "0 20 * * 0"
  time_zone   = "Australia/Brisbane"

  http_target {
    http_method = "POST"
    uri         = "${local.service_url}/trigger/weekly_report"
    
    oidc_token {
      service_account_email = google_service_account.agent_sa.email
    }
  }
}

# 4. Weekly Blogger Post (8 PM Sunday)
# NOTE: Usually you would pick EITHER #3 or #4, not both. They are separated here for completeness.
resource "google_cloud_scheduler_job" "weekly_blogger" {
  name        = "weekly-blogger-trigger"
  description = "Triggers the Weekly Publisher agent (Google Docs + Blogger)"
  schedule    = "0 20 * * 0"
  time_zone   = "Australia/Brisbane"

  http_target {
    http_method = "POST"
    uri         = "${local.service_url}/trigger/weekly_blogger"
    
    oidc_token {
      service_account_email = google_service_account.agent_sa.email
    }
  }
}
