variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, stag, prod)"
  type        = string
}

variable "region" {
  description = "The GCP region for the bucket"
  type        = string
}

variable "terraform_service_account_email" {
  description = "Email of the service account used by Terraform"
  type        = string
}

variable "project_number" {
  description = "The GCP project number (for Cloud Build service account)"
  type        = string
}

variable "kms_key_name" {
  description = "KMS key for bucket encryption (optional)"
  type        = string
  default     = ""
}

variable "access_logs_bucket" {
  description = "Bucket for storing access logs (optional)"
  type        = string
  default     = ""
}