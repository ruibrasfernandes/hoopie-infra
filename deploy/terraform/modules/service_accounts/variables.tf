variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, stag, prod)"
  type        = string
}

variable "servicenow_instance_url" {
  description = "ServiceNow instance URL - only required if secret doesn't exist"
  type        = string
  sensitive   = true
  default     = null
}

variable "servicenow_username" {
  description = "ServiceNow username - only required if secret doesn't exist"
  type        = string
  sensitive   = true
  default     = null
}

variable "servicenow_password" {
  description = "ServiceNow password - only required if secret doesn't exist"
  type        = string
  sensitive   = true
  default     = null
}

variable "mcp_bearer_token" {
  description = "MCP Bearer Token for Hoopie SDM - only required if secret doesn't exist"
  type        = string
  sensitive   = true
  default     = null
}

variable "project_number" {
  description = "The GCP project number (for Cloud Build service account)"
  type        = string
}