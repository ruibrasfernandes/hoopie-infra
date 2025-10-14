# Artifact Registry for container images
resource "google_artifact_registry_repository" "hoopie_repo" {
  location      = var.region
  repository_id = "hoopie-${var.environment}"
  description   = "Hoopie container repository for ${var.environment} environment"
  format        = "DOCKER"
  project       = var.project_id

  labels = {
    environment = var.environment
    managed-by  = "terraform"
  }

  lifecycle {
    ignore_changes = [labels]
  }

  # Cleanup policies for cost management
  cleanup_policies {
    id     = "keep-recent-versions"
    action = "KEEP"
    
    most_recent_versions {
      keep_count = 10
    }
  }

  cleanup_policies {
    id     = "delete-old-versions" 
    action = "DELETE"
    
    condition {
      older_than = "2592000s" # 30 days
    }
  }
}

# IAM binding for Cloud Build to push images
resource "google_artifact_registry_repository_iam_member" "cloudbuild_writer" {
  project    = var.project_id
  location   = google_artifact_registry_repository.hoopie_repo.location
  repository = google_artifact_registry_repository.hoopie_repo.name
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${var.project_number}@cloudbuild.gserviceaccount.com"
}

# IAM binding for service accounts to pull images
resource "google_artifact_registry_repository_iam_member" "mcp_server_reader" {
  project    = var.project_id
  location   = google_artifact_registry_repository.hoopie_repo.location
  repository = google_artifact_registry_repository.hoopie_repo.name
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${var.mcp_service_account_email}"
}