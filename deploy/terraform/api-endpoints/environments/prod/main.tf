terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  
  backend "gcs" {
    bucket = "hoopie-terraform-state-prod"
    prefix = "terraform/api-endpoints"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Data source to get existing API endpoints service account (created by infra)
data "google_service_account" "api_endpoints" {
  account_id = "hoopie-api-endpoints-${var.environment}"
  project    = var.project_id
}

# Create Cloud Run service for API endpoints
resource "google_cloud_run_v2_service" "api_endpoints" {
  name     = "api-endpoints-${var.environment}"
  location = var.region
  project  = var.project_id

  template {
    service_account = data.google_service_account.api_endpoints.email
    
    scaling {
      min_instance_count = var.environment == "prod" ? 1 : 0
      max_instance_count = var.environment == "prod" ? 10 : 3
    }

    containers {
      # Use the image built by Cloud Build
      image = "${var.region}-docker.pkg.dev/${var.project_id}/hoopie-${var.environment}/api-endpoints:latest"
      
      ports {
        container_port = 8080
      }

      resources {
        limits = {
          cpu    = var.environment == "prod" ? "2" : "1"
          memory = var.environment == "prod" ? "2Gi" : "1Gi"
        }
      }

      env {
        name = "ENVIRONMENT"
        value = var.environment
      }

      env {
        name = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }

      env {
        name = "GOOGLE_CLOUD_LOCATION"
        value = var.region
      }

    }
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }
}

# IAM policy to allow public access
resource "google_cloud_run_service_iam_member" "public_access" {
  location = google_cloud_run_v2_service.api_endpoints.location
  project  = google_cloud_run_v2_service.api_endpoints.project
  service  = google_cloud_run_v2_service.api_endpoints.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}