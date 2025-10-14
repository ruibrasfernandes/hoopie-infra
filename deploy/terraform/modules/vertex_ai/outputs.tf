output "staging_bucket_name" {
  description = "Name of the staging bucket for Vertex AI"
  value       = google_storage_bucket.staging_bucket.name
}

output "staging_bucket_url" {
  description = "URL of the staging bucket for Vertex AI"
  value       = "gs://${google_storage_bucket.staging_bucket.name}"
}