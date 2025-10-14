terraform {
  backend "gcs" {
    bucket = "hoopie-terraform-state-dev"
    prefix = "terraform/servicenow-mcp"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Data sources for existing resources
data "google_secret_manager_secret" "servicenow_instance_url" {
  secret_id = "servicenow-instance-url-${var.environment}"
  project   = var.project_id
}

data "google_secret_manager_secret" "servicenow_username" {
  secret_id = "servicenow-username-${var.environment}"
  project   = var.project_id
}

data "google_secret_manager_secret" "servicenow_password" {
  secret_id = "servicenow-password-${var.environment}"
  project   = var.project_id
}

data "google_secret_manager_secret" "mcp_bearer_token" {
  secret_id = "mcp-bearer-token-${var.environment}"
  project   = var.project_id
}

data "google_service_account" "mcp_server" {
  account_id = "hoopie-mcp-server-${var.environment}"
  project    = var.project_id
}

# Cloud Run service for ServiceNow MCP Server
resource "google_cloud_run_v2_service" "servicenow_mcp" {
  name     = "servicenow-mcp-${var.environment}"
  location = var.region
  project  = var.project_id
  
  deletion_protection = false

  template {
    service_account = data.google_service_account.mcp_server.email
    
    scaling {
      min_instance_count = var.environment == "prod" ? 1 : 0
      max_instance_count = var.environment == "prod" ? 10 : 3
    }

    containers {
      # Use the latest built image
      image = "${var.region}-docker.pkg.dev/${var.project_id}/hoopie-${var.environment}/servicenow-mcp:latest"
      
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
        name  = "ENVIRONMENT"
        value = var.environment
      }

      env {
        name = "SERVICENOW_INSTANCE_URL"
        value_source {
          secret_key_ref {
            secret  = data.google_secret_manager_secret.servicenow_instance_url.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "SERVICENOW_USERNAME"
        value_source {
          secret_key_ref {
            secret  = data.google_secret_manager_secret.servicenow_username.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "SERVICENOW_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = data.google_secret_manager_secret.servicenow_password.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "MCP_BEARER_TOKEN"
        value_source {
          secret_key_ref {
            secret  = data.google_secret_manager_secret.mcp_bearer_token.secret_id
            version = "latest"
          }
        }
      }

      env {
        name  = "SERVICENOW_AUTH_TYPE"
        value = "basic"
      }

      env {
        name  = "MCP_TOOL_PACKAGE"
        value = "full"
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
  location = google_cloud_run_v2_service.servicenow_mcp.location
  project  = google_cloud_run_v2_service.servicenow_mcp.project
  service  = google_cloud_run_v2_service.servicenow_mcp.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}