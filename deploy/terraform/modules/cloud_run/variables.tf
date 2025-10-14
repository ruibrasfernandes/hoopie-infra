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

variable "service_account_email" {
  description = "Service account email for Cloud Run"
  type        = string
}

variable "servicenow_mcp_image" {
  description = "ServiceNow MCP container image URL"
  type        = string
  default     = ""
}

