# Terraform state bucket module
# This creates and manages the GCS bucket used for Terraform state

resource "google_storage_bucket" "terraform_state" {
  name          = "hoopie-terraform-state-${var.environment}"
  location      = var.region
  project       = var.project_id
  force_destroy = false

  # Enable versioning for state history
  versioning {
    enabled = true
  }

  # Lifecycle management for old versions
  lifecycle_rule {
    condition {
      age                   = 90
      with_state           = "ARCHIVED"
      num_newer_versions   = 5
    }
    action {
      type = "Delete"
    }
  }

  # Archive old versions after 30 days
  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }

  # Uniform bucket-level access
  uniform_bucket_level_access = true

  # Prevent accidental deletion
  lifecycle {
    prevent_destroy = true
  }

  # Encryption
  encryption {
    default_kms_key_name = var.kms_key_name
  }

  # Logging (if access logging bucket is provided)
  dynamic "logging" {
    for_each = var.access_logs_bucket != "" ? [1] : []
    content {
      log_bucket   = var.access_logs_bucket
      log_object_prefix = "terraform-state-access-logs/"
    }
  }

  labels = {
    environment = var.environment
    purpose     = "terraform-state"
    managed-by  = "terraform"
  }
}

# IAM binding for Terraform service account
resource "google_storage_bucket_iam_member" "terraform_state_admin" {
  bucket = google_storage_bucket.terraform_state.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.terraform_service_account_email}"
}

# IAM binding for Cloud Build service account
resource "google_storage_bucket_iam_member" "cloudbuild_state_admin" {
  bucket = google_storage_bucket.terraform_state.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.project_number}@cloudbuild.gserviceaccount.com"
}