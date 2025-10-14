variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, stag, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "stag", "prod"], var.environment)
    error_message = "Environment must be one of: dev, stag, prod."
  }
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "europe-southwest1"
}

variable "zone" {
  description = "The GCP zone"
  type        = string
  default     = "europe-southwest1-a"
}

variable "servicenow_instance_url" {
  description = "ServiceNow instance URL"
  type        = string
  sensitive   = true
}

variable "servicenow_username" {
  description = "ServiceNow username"
  type        = string
  sensitive   = true
}

variable "servicenow_password" {
  description = "ServiceNow password"
  type        = string
  sensitive   = true
}