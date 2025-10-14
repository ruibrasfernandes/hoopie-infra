variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, stag, prod)"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
}

variable "adk_agent_service_account_email" {
  description = "Email of the ADK agent service account"
  type        = string
}

variable "adk_agent_service_account_key" {
  description = "Private key for ADK agent service account"
  type        = string
  sensitive   = true
}

variable "cloudbuild_service_account_email" {
  description = "Email of the dedicated Cloud Build service account"
  type        = string
}