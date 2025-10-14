#!/bin/bash

# Fix Terraform service account permissions
# Run this if you get "iam.serviceaccounts.actAs" permission denied errors

set -e

ENV=${1:-dev}
PROJECT_ID="hoopie-${ENV}"

echo "Fixing Terraform service account permissions for environment: $ENV"
echo "Project: $PROJECT_ID"

TERRAFORM_SA="terraform-deployer-$ENV@$PROJECT_ID.iam.gserviceaccount.com"

# Add Service Account User role (needed to create Cloud Run services with service accounts)
echo "🔧 Adding Service Account User role..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$TERRAFORM_SA" \
    --role="roles/iam.serviceAccountUser"

# Also grant direct permission to act as the MCP service account
echo "🔧 Granting permission to act as MCP service account..."
gcloud iam service-accounts add-iam-policy-binding \
    hoopie-mcp-server-$ENV@$PROJECT_ID.iam.gserviceaccount.com \
    --member="serviceAccount:$TERRAFORM_SA" \
    --role="roles/iam.serviceAccountUser" \
    --project=$PROJECT_ID

# Grant permission to act as ADK service account too
echo "🔧 Granting permission to act as ADK service account..."
gcloud iam service-accounts add-iam-policy-binding \
    hoopie-adk-agent-$ENV@$PROJECT_ID.iam.gserviceaccount.com \
    --member="serviceAccount:$TERRAFORM_SA" \
    --role="roles/iam.serviceAccountUser" \
    --project=$PROJECT_ID

echo "✅ Terraform service account permissions fixed!"
echo "   Now retry: ./deploy.sh $ENV infra"