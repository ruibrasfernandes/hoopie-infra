# Cloud Run service for ServiceNow MCP Server
resource "google_cloud_run_v2_service" "servicenow_mcp" {
  name     = "servicenow-mcp-${var.environment}"
  location = var.region
  project  = var.project_id
  
  deletion_protection = false

  template {
    service_account = var.service_account_email
    
    scaling {
      min_instance_count = var.environment == "prod" ? 1 : 0
      max_instance_count = var.environment == "prod" ? 10 : 3
    }

    containers {
      # Use a placeholder image initially - will be updated when actual image is built
      image = var.servicenow_mcp_image != "" ? var.servicenow_mcp_image : "gcr.io/cloudshell-images/cloudshell:latest"
      
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
        name = "SERVICENOW_INSTANCE_URL"
        value_source {
          secret_key_ref {
            secret  = "servicenow-instance-url-${var.environment}"
            version = "latest"
          }
        }
      }

      env {
        name = "SERVICENOW_USERNAME"
        value_source {
          secret_key_ref {
            secret  = "servicenow-username-${var.environment}"
            version = "latest"
          }
        }
      }

      env {
        name = "SERVICENOW_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = "servicenow-password-${var.environment}"
            version = "latest"
          }
        }
      }

      env {
        name = "SERVICENOW_AUTH_TYPE"
        value = "basic"
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

# Note: Secrets and IAM bindings are managed by the service_accounts module
# Cloud Run references the secrets directly by ID