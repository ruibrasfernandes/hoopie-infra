#!/bin/bash

# Quick deploy script for ServiceNow MCP Server
# Simple one-liner deployment with minimal output

set -e

echo "🚀 Deploying ServiceNow MCP Server..."

# Check if gcloud is available
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI not found. Please install it first."
    exit 1
fi

# Get current project
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: No project set. Run 'gcloud config set project PROJECT_ID' first."
    exit 1
fi

# Submit build
echo "📦 Building and deploying to project: $PROJECT_ID"
gcloud builds submit --config cloudbuild.yaml --quiet

# Get service URL
SERVICE_URL=$(gcloud run services describe servicenow-mcp --region=europe-southwest1 --format="value(status.url)" 2>/dev/null)

if [ -n "$SERVICE_URL" ]; then
    echo "✅ Deployment successful!"
    echo "🌐 Service URL: $SERVICE_URL"
    echo "🔍 Test: curl $SERVICE_URL/health"
    echo "🔧 MCP Inspector: npx @modelcontextprotocol/inspector $SERVICE_URL/sse"
else
    echo "❌ Deployment may have failed. Check Cloud Console for details."
    exit 1
fi