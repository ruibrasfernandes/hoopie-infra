
output "staging_bucket_url" {
  description = "URL of the Vertex AI staging bucket"
  value       = module.vertex_ai.staging_bucket_url
}

output "mcp_server_service_account_email" {
  description = "Email of the MCP server service account"
  value       = module.service_accounts.mcp_server_service_account_email
}

output "adk_agent_service_account_email" {
  description = "Email of the ADK agent service account"
  value       = module.service_accounts.adk_agent_service_account_email
}