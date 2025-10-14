# Service Account for MCP Server
resource "google_service_account" "mcp_server" {
  account_id   = "hoopie-mcp-server-${var.environment}"
  display_name = "Hoopie MCP Server Service Account - ${title(var.environment)}"
  description  = "Service account for Hoopie ServiceNow MCP server in ${var.environment} environment"
  project      = var.project_id
}

# Service Account for ADK Agent
resource "google_service_account" "adk_agent" {
  account_id   = "hoopie-adk-agent-${var.environment}"
  display_name = "Hoopie ADK Agent Service Account - ${title(var.environment)}"
  description  = "Service account for Hoopie ADK agent in ${var.environment} environment"
  project      = var.project_id
}

# Service Account for API Endpoints
resource "google_service_account" "api_endpoints" {
  account_id   = "hoopie-api-endpoints-${var.environment}"
  display_name = "Hoopie API Endpoints Service Account - ${title(var.environment)}"
  description  = "Service account for Hoopie API endpoints in ${var.environment} environment"
  project      = var.project_id
}

# Service Account for Cloud Build Deployments
resource "google_service_account" "cloudbuild_deployer" {
  account_id   = "hoopie-cloudbuild-${var.environment}"
  display_name = "Hoopie Cloud Build Deployer - ${title(var.environment)}"
  description  = "Dedicated service account for Cloud Build deployments in ${var.environment} environment"
  project      = var.project_id

  lifecycle {
    ignore_changes = [display_name, description]
  }
}

# IAM bindings for MCP Server
resource "google_project_iam_member" "mcp_server_roles" {
  for_each = toset([
    "roles/run.invoker",
    "roles/run.developer",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/secretmanager.secretAccessor"
  ])
  
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.mcp_server.email}"
}

# IAM bindings for ADK Agent
resource "google_project_iam_member" "adk_agent_roles" {
  for_each = toset([
    "roles/aiplatform.user",
    "roles/aiplatform.serviceAgent",
    "roles/storage.objectViewer",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/secretmanager.secretAccessor",
    "roles/run.invoker"
  ])
  
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.adk_agent.email}"
}

# IAM bindings for API Endpoints
resource "google_project_iam_member" "api_endpoints_roles" {
  for_each = toset([
    "roles/aiplatform.user",
    "roles/aiplatform.admin",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/run.invoker"
  ])
  
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.api_endpoints.email}"
}

# Service Account Key for MCP Server (for external access)
resource "google_service_account_key" "mcp_server_key" {
  service_account_id = google_service_account.mcp_server.name
  public_key_type    = "TYPE_X509_PEM_FILE"
}

# Service Account Key for ADK Agent
resource "google_service_account_key" "adk_agent_key" {
  service_account_id = google_service_account.adk_agent.name
  public_key_type    = "TYPE_X509_PEM_FILE"
}

# Grant the Terraform service account permission to act as these service accounts
# This is needed for Cloud Run to use these service accounts
data "google_client_config" "current" {}

locals {
  terraform_sa_email = "terraform-deployer-${var.environment}@${var.project_id}.iam.gserviceaccount.com"
}

resource "google_service_account_iam_member" "terraform_can_act_as_mcp" {
  service_account_id = google_service_account.mcp_server.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${local.terraform_sa_email}"
}

resource "google_service_account_iam_member" "terraform_can_act_as_adk" {
  service_account_id = google_service_account.adk_agent.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${local.terraform_sa_email}"
}

resource "google_service_account_iam_member" "terraform_can_act_as_api_endpoints" {
  service_account_id = google_service_account.api_endpoints.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${local.terraform_sa_email}"
}

# MCP Bearer Token Secret - always try to create, will be ignored if exists
resource "google_secret_manager_secret" "mcp_bearer_token" {
  secret_id = "mcp-bearer-token-${var.environment}"
  project   = var.project_id

  replication {
    auto {}
  }
  
  lifecycle {
    ignore_changes = [labels]
  }
}

resource "google_secret_manager_secret_version" "mcp_bearer_token" {
  count       = var.mcp_bearer_token != null ? 1 : 0
  secret      = google_secret_manager_secret.mcp_bearer_token.id
  secret_data = var.mcp_bearer_token
  
  lifecycle {
    ignore_changes = [secret_data]
  }
}

# IAM binding for MCP bearer token secret
resource "google_secret_manager_secret_iam_member" "mcp_bearer_token_access" {
  secret_id = google_secret_manager_secret.mcp_bearer_token.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.mcp_server.email}"
}

# ServiceNow Credentials Secrets - only create if values are provided (first time deployment)
resource "google_secret_manager_secret" "servicenow_instance_url" {
  count     = var.servicenow_instance_url != null ? 1 : 0
  secret_id = "servicenow-instance-url-${var.environment}"
  project   = var.project_id

  replication {
    auto {}
  }
  
  lifecycle {
    ignore_changes = [labels]
  }
}

resource "google_secret_manager_secret_version" "servicenow_instance_url" {
  count       = var.servicenow_instance_url != null ? 1 : 0
  secret      = google_secret_manager_secret.servicenow_instance_url[0].id
  secret_data = var.servicenow_instance_url
  
  lifecycle {
    ignore_changes = [secret_data]
  }
}

resource "google_secret_manager_secret" "servicenow_username" {
  count     = var.servicenow_username != null ? 1 : 0
  secret_id = "servicenow-username-${var.environment}"
  project   = var.project_id

  replication {
    auto {}
  }
  
  lifecycle {
    ignore_changes = [labels]
  }
}

resource "google_secret_manager_secret_version" "servicenow_username" {
  count       = var.servicenow_username != null ? 1 : 0
  secret      = google_secret_manager_secret.servicenow_username[0].id
  secret_data = var.servicenow_username
  
  lifecycle {
    ignore_changes = [secret_data]
  }
}

resource "google_secret_manager_secret" "servicenow_password" {
  count     = var.servicenow_password != null ? 1 : 0
  secret_id = "servicenow-password-${var.environment}"
  project   = var.project_id

  replication {
    auto {}
  }
  
  lifecycle {
    ignore_changes = [labels]
  }
}

resource "google_secret_manager_secret_version" "servicenow_password" {
  count       = var.servicenow_password != null ? 1 : 0
  secret      = google_secret_manager_secret.servicenow_password[0].id
  secret_data = var.servicenow_password
  
  lifecycle {
    ignore_changes = [secret_data]
  }
}

# IAM bindings for ServiceNow secrets - always try to create, will work with existing secrets
resource "google_secret_manager_secret_iam_member" "servicenow_instance_url_access" {
  secret_id = "servicenow-instance-url-${var.environment}"
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.mcp_server.email}"
  
  depends_on = [
    google_secret_manager_secret.servicenow_instance_url,
    google_secret_manager_secret_version.servicenow_instance_url
  ]
}

resource "google_secret_manager_secret_iam_member" "servicenow_username_access" {
  secret_id = "servicenow-username-${var.environment}"
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.mcp_server.email}"
  
  depends_on = [
    google_secret_manager_secret.servicenow_username,
    google_secret_manager_secret_version.servicenow_username
  ]
}

resource "google_secret_manager_secret_iam_member" "servicenow_password_access" {
  secret_id = "servicenow-password-${var.environment}"
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.mcp_server.email}"
  
  depends_on = [
    google_secret_manager_secret.servicenow_password,
    google_secret_manager_secret_version.servicenow_password
  ]
}

# IAM bindings for Cloud Build Deployer
resource "google_project_iam_member" "cloudbuild_deployer_roles" {
  for_each = toset([
    "roles/secretmanager.secretAccessor",
    "roles/storage.admin",
    "roles/artifactregistry.writer",
    "roles/run.admin",  # Changed from run.developer to run.admin to allow setting IAM policies
    "roles/aiplatform.admin",
    "roles/logging.logWriter",
    "roles/cloudbuild.builds.editor",
    "roles/iam.serviceAccountUser"
  ])
  
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.cloudbuild_deployer.email}"
}