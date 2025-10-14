output "mcp_server_service_account_email" {
  description = "Email of the MCP server service account"
  value       = google_service_account.mcp_server.email
}

output "mcp_server_service_account_key" {
  description = "Private key for MCP server service account"
  value       = google_service_account_key.mcp_server_key.private_key
  sensitive   = true
}

output "adk_agent_service_account_email" {
  description = "Email of the ADK agent service account"
  value       = google_service_account.adk_agent.email
}

output "adk_agent_service_account_key" {
  description = "Private key for ADK agent service account"
  value       = google_service_account_key.adk_agent_key.private_key
  sensitive   = true
}

output "api_endpoints_service_account_email" {
  description = "Email of the API endpoints service account"
  value       = google_service_account.api_endpoints.email
}

output "cloudbuild_deployer_service_account_email" {
  description = "Email of the Cloud Build deployer service account"
  value       = google_service_account.cloudbuild_deployer.email
}