variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "europe-southwest1"
}

variable "environment" {
  description = "Environment name (dev, stag, prod)"
  type        = string
  default     = "prod"
}