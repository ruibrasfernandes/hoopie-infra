output "api_endpoints_service_url" {
  description = "URL of the deployed API endpoints service"
  value       = google_cloud_run_v2_service.api_endpoints.uri
}

output "api_endpoints_service_name" {
  description = "Name of the API endpoints service"
  value       = google_cloud_run_v2_service.api_endpoints.name
}