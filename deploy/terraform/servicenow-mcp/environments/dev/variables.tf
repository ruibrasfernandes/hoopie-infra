variable "project_id" {
  description = "The GCP project ID"
  type        = string
  default     = "hoopie-test"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "europe-southwest1"
}