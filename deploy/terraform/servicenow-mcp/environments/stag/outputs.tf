output "servicenow_mcp_url" {
  description = "URL of the ServiceNow MCP service"
  value       = google_cloud_run_v2_service.servicenow_mcp.uri
}

output "servicenow_mcp_service_name" {
  description = "Name of the ServiceNow MCP service"
  value       = google_cloud_run_v2_service.servicenow_mcp.name
}