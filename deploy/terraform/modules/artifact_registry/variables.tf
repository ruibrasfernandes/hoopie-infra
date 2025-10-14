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

variable "project_number" {
  description = "The GCP project number"
  type        = string
}

variable "mcp_service_account_email" {
  description = "Email of the MCP service account"
  type        = string
}