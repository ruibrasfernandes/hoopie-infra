terraform {
  backend "gcs" {
    bucket = "hoopie-terraform-state-stag" # This will be updated per environment
    prefix = "terraform/cloud-run"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Get project data
data "google_project" "project" {
  project_id = var.project_id
}

# Reference existing service account created by infrastructure
data "google_service_account" "mcp_server" {
  account_id = "hoopie-mcp-server-${var.environment}"
  project    = var.project_id
}

# Cloud Run module for ServiceNow MCP
module "cloud_run" {
  source = "../modules/cloud_run"
  
  project_id              = var.project_id
  environment             = var.environment
  region                  = var.region
  service_account_email   = data.google_service_account.mcp_server.email
  servicenow_mcp_image    = var.servicenow_mcp_image
}