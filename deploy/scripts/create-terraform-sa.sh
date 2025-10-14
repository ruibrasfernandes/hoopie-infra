#!/bin/bash

# Create a dedicated Terraform service account with elevated permissions
# This needs to be run once manually by a project owner

set -e

ENV=${1:-dev}
PROJECT_ID="hoopie-${ENV}"

echo "Creating Terraform service account for environment: $ENV"
echo "Project: $PROJECT_ID"

# Create the service account
gcloud iam service-accounts create terraform-deployer-$ENV \
    --display-name="Terraform Deployer for $ENV" \
    --description="Service account for Terraform deployments in $ENV environment" \
    --project=$PROJECT_ID

TERRAFORM_SA="terraform-deployer-$ENV@$PROJECT_ID.iam.gserviceaccount.com"

echo "🔧 Granting necessary permissions to Terraform service account..."

# Core permissions for Terraform
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$TERRAFORM_SA" \
    --role="roles/compute.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$TERRAFORM_SA" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$TERRAFORM_SA" \
    --role="roles/iam.serviceAccountAdmin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$TERRAFORM_SA" \
    --role="roles/iam.serviceAccountKeyAdmin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$TERRAFORM_SA" \
    --role="roles/resourcemanager.projectIamAdmin"

# Cloud Run permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$TERRAFORM_SA" \
    --role="roles/run.admin"

# Secret Manager permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$TERRAFORM_SA" \
    --role="roles/secretmanager.admin"

# Artifact Registry permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$TERRAFORM_SA" \
    --role="roles/artifactregistry.admin"

# Vertex AI permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$TERRAFORM_SA" \
    --role="roles/aiplatform.admin"

# Logging and monitoring
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$TERRAFORM_SA" \
    --role="roles/logging.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$TERRAFORM_SA" \
    --role="roles/monitoring.admin"

# Service Account User role (needed to create Cloud Run services with service accounts)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$TERRAFORM_SA" \
    --role="roles/iam.serviceAccountUser"

# Grant Cloud Build permission to impersonate this service account
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
gcloud iam service-accounts add-iam-policy-binding $TERRAFORM_SA \
    --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
    --role="roles/iam.serviceAccountTokenCreator" \
    --project=$PROJECT_ID

echo "✅ Terraform service account created and configured successfully!"
echo "   Service Account: $TERRAFORM_SA"
echo ""
echo "📝 Next steps:"
echo "   1. Update cloudbuild-infra.yaml to use this service account"
echo "   2. Restore IAM bindings to Terraform configurations"
echo "   3. Deploy infrastructure using: ./deploy.sh $ENV infra"