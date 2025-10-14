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