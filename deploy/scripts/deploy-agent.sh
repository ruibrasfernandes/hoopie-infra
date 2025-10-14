#!/bin/bash

# Deploy script for Hoopie SDM Agent
# This script deploys the Service Delivery Manager agent to Vertex AI

#!/bin/bash

# Ask for project to deploy in
if [ -z "$1" ]
then
      echo "please use: $0 {dev/stag/prod}"
      exit
fi

# GET Project Variables
case $1 in
    "stag")
        echo "Deploying in Staging environment"
        # source .env.stag
        ENV_FILE=".env.stag"

        ;;
    "dev")
        echo "Deploying in DEV environment"
        # source .env.dev
        ENV_FILE=".env.dev"
        ;;
    "prod")
        echo "Deploying in PROD environment"
        # source .env.prod
        ENV_FILE=".env.prod"
        ;;
    *)
        echo "Not possible to deploy in $1"
        exit
esac

# ... Adapting from "ENV_VAR=VALUE" to "export ENV_VAR=VALUE"

if [ -f "$ENV_FILE" ]; then
    while IFS='=' read -r key value; do
        if [[ ! -z "$key" && ! "$key" =~ ^# ]]; then # Ensure key is not empty and not a comment
            export "$key=$value"
        fi
    done < "$ENV_FILE"
else
    echo "Warning: .env file not found at $ENV_FILE, using default values"
    # Set default values for dev environment
    export GOOGLE_CLOUD_PROJECT="hoopie-dev"
    export GOOGLE_CLOUD_LOCATION="europe-southwest1"
    export STAGING_BUCKET="hoopie-dev-agent"
    export MCP_BEARER_TOKEN="hoopie-secure-token-2025"
    export APP_NAME="Hoopie SDM Agent (Dev)"
fi

echo "Project: $GOOGLE_CLOUD_PROJECT"
echo "ProjectId: $PROJECT_ID"
echo "Location: $GOOGLE_CLOUD_LOCATION"
echo "Using Vertex AI: $GOOGLE_GENAI_USE_VERTEXAI"
echo "Staging Bucket: $STAGING_BUCKET"
echo "Environment: $ENVIRONMENT"
echo "App name: $APP_NAME"


set -e  # Exit on any error

echo "🚀 Deploying Hoopie SDM Agent..."

# Check if we're in the right directory (root of hoopie-adk)
if [ ! -f "requirements.txt" ] || [ ! -d "hoopie_sdm" ]; then
    echo "❌ Error: Please run this script from the hoopie-adk root directory."
    echo "   Expected files: requirements.txt, hoopie_sdm/ directory"
    exit 1
fi

# Check if MCP_BEARER_TOKEN is set
if [ -z "$MCP_BEARER_TOKEN" ]; then
    echo "❌ Error: MCP_BEARER_TOKEN environment variable is not set."
    echo "   Please set it with: export MCP_BEARER_TOKEN=hoopie-secure-token-2025"
    exit 1
fi

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Error: Not authenticated with gcloud. Please run: gcloud auth login"
    exit 1
fi

# Set the correct project
echo "🔧 Setting GCP project..."
gcloud config set project $GOOGLE_CLOUD_PROJECT

# Create staging bucket if it doesn't exist
echo "🪣 Checking staging bucket..."
# Ensure STAGING_BUCKET has the correct gs:// format
if [[ ! "$STAGING_BUCKET" =~ ^gs:// ]]; then
    STAGING_BUCKET="gs://$STAGING_BUCKET"
fi

if ! gsutil ls $STAGING_BUCKET > /dev/null 2>&1; then
    echo "Creating staging bucket: $STAGING_BUCKET"
    gsutil mb -p $GOOGLE_CLOUD_PROJECT -l $GOOGLE_CLOUD_LOCATION $STAGING_BUCKET
else
    echo "Staging bucket already exists: $STAGING_BUCKET"
fi

# Deploy the agent using ADK
echo "📦 Deploying agent with ADK..."
uv run adk deploy agent_engine \
    --project=$GOOGLE_CLOUD_PROJECT \
    --region=$GOOGLE_CLOUD_LOCATION \
    --staging_bucket=$STAGING_BUCKET \
    --display_name="$APP_NAME" \
    --description="Service Delivery Manager with ServiceNow MCP integration" \
    --requirements_file=requirements.txt \
    --adk_app=hoopie_sdm.agent \
    .

#     --env_file=hoopie_sdm/.env \


echo "✅ Agent deployment completed successfully!"
echo "🌍 Region: $GOOGLE_CLOUD_LOCATION"
echo "📁 Project: $GOOGLE_CLOUD_PROJECT"
echo ""
echo "⚠️  Note: A new agent will be created with each deployment."
echo "   You may need to update your proxy service with the new agent ID."
echo "   Check the deployment output above for the new reasoning engine ID."