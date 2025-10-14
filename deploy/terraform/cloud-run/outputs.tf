output "servicenow_mcp_url" {
  description = "URL of the ServiceNow MCP Cloud Run service"
  value       = module.cloud_run.servicenow_mcp_url
}

output "servicenow_mcp_service_name" {
  description = "Name of the ServiceNow MCP Cloud Run service"
  value       = module.cloud_run.servicenow_mcp_service_name
}