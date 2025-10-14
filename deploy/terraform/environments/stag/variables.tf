variable "project_id" {
  description = "The GCP project ID"
  type        = string
  default     = "hoopie-stag"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "stag"
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "europe-southwest1"
}

variable "servicenow_instance_url" {
  description = "ServiceNow instance URL - only required if secret doesn't exist in Secret Manager"
  type        = string
  sensitive   = true
  default     = null
}

variable "servicenow_username" {
  description = "ServiceNow username - only required if secret doesn't exist in Secret Manager"
  type        = string
  sensitive   = true
  default     = null
}

variable "servicenow_password" {
  description = "ServiceNow password - only required if secret doesn't exist in Secret Manager"
  type        = string
  sensitive   = true
  default     = null
}

variable "mcp_bearer_token" {
  description = "MCP Bearer Token for Hoopie SDM - only required if secret doesn't exist in Secret Manager"
  type        = string
  sensitive   = true
  default     = null
}

variable "servicenow_mcp_image" {
  description = "ServiceNow MCP container image URL"
  type        = string
  default     = ""
}

