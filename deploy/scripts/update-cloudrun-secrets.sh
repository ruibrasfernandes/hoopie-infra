#!/bin/bash

# Update Cloud Run service to use Secret Manager after IAM setup
# This script redeploys the Cloud Run service with secrets enabled

set -e

ENV=${1:-dev}
PROJECT_ID="hoopie-${ENV}"

echo "Updating Cloud Run service to use Secret Manager secrets for environment: $ENV"
echo "Project: $PROJECT_ID"

# Check if infrastructure is deployed
if [ ! -d "../terraform/environments/$ENV" ]; then
    echo "❌ Environment directory not found: ../terraform/environments/$ENV"
    exit 1
fi

# Update the Cloud Run service to use secrets
cd ../terraform/environments/$ENV

echo "🔧 Updating Cloud Run service configuration to use secrets..."

# Set the use_secrets variable to true and apply
terraform apply \
    -var="use_secrets=true" \
    -target="module.cloud_run.google_cloud_run_v2_service.servicenow_mcp" \
    -auto-approve

cd ../../../..

echo "✅ Cloud Run service updated to use Secret Manager secrets!"
echo "   The service will now securely access ServiceNow credentials from Secret Manager"