terraform {
  backend "gcs" {
    bucket = "hoopie-terraform-state-stag"
    prefix = "terraform/state"
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

data "google_project" "project" {
  project_id = var.project_id
}

module "artifact_registry" {
  source = "../../modules/artifact_registry"
  
  project_id                = var.project_id
  environment               = var.environment
  region                    = var.region
  project_number            = data.google_project.project.number
  mcp_service_account_email = module.service_accounts.mcp_server_service_account_email
}

module "service_accounts" {
  source = "../../modules/service_accounts"
  
  project_id              = var.project_id
  project_number          = data.google_project.project.number
  environment             = var.environment
  servicenow_instance_url = var.servicenow_instance_url
  servicenow_username     = var.servicenow_username
  servicenow_password     = var.servicenow_password
  mcp_bearer_token        = var.mcp_bearer_token
}


# Note: cloud_run module is deployed separately via servicenow_mcp component
# It should not be part of the infrastructure deployment

module "vertex_ai" {
  source = "../../modules/vertex_ai"
  
  project_id                        = var.project_id
  environment                       = var.environment
  region                            = var.region
  adk_agent_service_account_email   = module.service_accounts.adk_agent_service_account_email
  adk_agent_service_account_key     = module.service_accounts.adk_agent_service_account_key
  cloudbuild_service_account_email  = module.service_accounts.cloudbuild_deployer_service_account_email
}