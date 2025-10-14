# Vertex AI Agent Engine resources
resource "google_storage_bucket" "staging_bucket" {
  name          = "hoopie-staging-${var.environment}-${random_string.bucket_suffix.result}"
  location      = var.region
  project       = var.project_id
  force_destroy = var.environment != "prod"

  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = var.environment == "prod" ? 90 : 30
    }
    action {
      type = "Delete"
    }
  }
}

resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

# IAM binding for the ADK agent service account to access the staging bucket
resource "google_storage_bucket_iam_member" "staging_bucket_access" {
  bucket = google_storage_bucket.staging_bucket.name
  role   = "roles/storage.admin"
  member = "serviceAccount:${var.adk_agent_service_account_email}"
}

# Secret for ADK agent service account key
resource "google_secret_manager_secret" "adk_agent_key" {
  secret_id = "adk-agent-key-${var.environment}"
  project   = var.project_id

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "adk_agent_key" {
  secret      = google_secret_manager_secret.adk_agent_key.id
  secret_data = base64decode(var.adk_agent_service_account_key)
}

# Grant Cloud Build access to the ADK agent key specifically
resource "google_secret_manager_secret_iam_member" "cloudbuild_adk_agent_key_access" {
  secret_id = google_secret_manager_secret.adk_agent_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.cloudbuild_service_account_email}"
}