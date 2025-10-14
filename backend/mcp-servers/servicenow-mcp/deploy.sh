#!/bin/bash

# Deploy script for ServiceNow MCP Server to Google Cloud Run
# This script builds and deploys the ServiceNow MCP server using Google Cloud Build
# Usage: ./deploy.sh <environment>
# Environment: dev, stag, prod

set -e  # Exit on any error

# Check if environment argument is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <environment>"
    echo "Environment options: dev, stag, prod"
    exit 1
fi

ENVIRONMENT=$1

# Validate environment
case $ENVIRONMENT in
    dev|stag|prod)
        echo "Deploying to $ENVIRONMENT environment..."
        ;;
    *)
        echo "Invalid environment: $ENVIRONMENT"
        echo "Valid options: dev, stag, prod"
        exit 1
        ;;
esac

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Load environment-specific configuration
ENV_FILE=".env.${ENVIRONMENT}"

if [ ! -f "$ENV_FILE" ]; then
    print_error "Environment file $ENV_FILE not found."
    exit 1
fi

print_status "Loading configuration from $ENV_FILE"

# Load environment variables from the file
set -a  # automatically export all variables
source "$ENV_FILE"
set +a  # stop automatically exporting

# Validate required environment variables
if [ -z "$GOOGLE_CLOUD_PROJECT" ]; then
    print_error "GOOGLE_CLOUD_PROJECT not found in $ENV_FILE"
    exit 1
fi

if [ -z "$GOOGLE_CLOUD_LOCATION" ]; then
    print_error "GOOGLE_CLOUD_LOCATION not found in $ENV_FILE"
    exit 1
fi

print_status "Project: $GOOGLE_CLOUD_PROJECT"
print_status "Location: $GOOGLE_CLOUD_LOCATION"

# Set the project for gcloud
gcloud config set project "$GOOGLE_CLOUD_PROJECT"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    print_error "You are not authenticated with gcloud. Please run 'gcloud auth login' first."
    exit 1
fi

print_status "Deploying ServiceNow MCP Server to Google Cloud Run..."
print_status "Environment: $ENVIRONMENT"
print_status "Project: $GOOGLE_CLOUD_PROJECT"
print_status "Location: $GOOGLE_CLOUD_LOCATION"

# Use the PROJECT_ID from environment for compatibility
PROJECT_ID=$GOOGLE_CLOUD_PROJECT

# Check if cloudbuild.yaml exists
if [ ! -f "cloudbuild.yaml" ]; then
    print_error "cloudbuild.yaml not found. Make sure you're in the correct directory."
    exit 1
fi

# Basic checks
print_status "Running basic checks..."

# Simple note about prerequisites  
print_warning "Make sure you have:"
print_warning "  1. Artifact Registry repository 'hoopie-agents' created in $GOOGLE_CLOUD_LOCATION"
print_warning "  2. Cloud Build API enabled"
print_warning "  3. Cloud Run API enabled"
print_warning "  4. Appropriate permissions for Cloud Build and Cloud Run"
print_warning ""
print_warning "If the build fails, check the error message for missing prerequisites."

# Start the build
print_status "Starting Google Cloud Build..."
echo "----------------------------------------"

# Submit the build with environment substitutions and capture the build ID
print_status "Submitting build with substitutions:"
print_status "  _ENVIRONMENT=$ENVIRONMENT"
print_status "  _GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT"
print_status "  _GOOGLE_CLOUD_LOCATION=$GOOGLE_CLOUD_LOCATION"

BUILD_OUTPUT=$(gcloud builds submit --config cloudbuild.yaml \
    --substitutions="_ENVIRONMENT=$ENVIRONMENT,_GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT,_GOOGLE_CLOUD_LOCATION=$GOOGLE_CLOUD_LOCATION" \
    --format="value(id)" 2>&1)
BUILD_SUBMIT_EXIT_CODE=$?
BUILD_ID=$(echo "$BUILD_OUTPUT" | tail -n 1)

if [ $BUILD_SUBMIT_EXIT_CODE -eq 0 ] && [[ "$BUILD_ID" =~ ^[a-f0-9-]{36}$ ]]; then
    print_success "Build submitted successfully!"
    print_status "Build ID: $BUILD_ID"
    print_status "You can monitor the build progress at:"
    echo "https://console.cloud.google.com/cloud-build/builds/$BUILD_ID?project=$PROJECT_ID"
    
    # Wait for build to complete
    print_status "Waiting for build to complete..."
    
    # Stream logs and capture any streaming errors
    STREAM_OUTPUT=$(gcloud builds log --stream $BUILD_ID 2>&1)
    STREAM_EXIT_CODE=$?
    
    if [ $STREAM_EXIT_CODE -ne 0 ]; then
        print_warning "Issue streaming logs, but checking build status..."
        print_status "Stream output: $STREAM_OUTPUT"
    fi
    
    # Check build status with error handling
    BUILD_STATUS=$(gcloud builds describe $BUILD_ID --format="value(status)" 2>/dev/null)
    DESCRIBE_EXIT_CODE=$?
    
    if [ $DESCRIBE_EXIT_CODE -ne 0 ]; then
        print_error "Failed to get build status for build ID: $BUILD_ID"
        print_error "This might indicate a problem with the build submission or permissions."
        print_status "You can check the build manually at:"
        echo "https://console.cloud.google.com/cloud-build/builds/$BUILD_ID?project=$PROJECT_ID"
        exit 1
    fi
    
    if [ "$BUILD_STATUS" = "SUCCESS" ]; then
        print_success "Deployment completed successfully!"
        
        # Get the service URL
        SERVICE_NAME="servicenow-mcp-$ENVIRONMENT"
        SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$GOOGLE_CLOUD_LOCATION --format="value(status.url)")
        
        print_success "ServiceNow MCP Server is now running at:"
        echo "$SERVICE_URL"
        
        echo ""
        print_status "Quick test commands:"
        echo "# Test health endpoint:"
        echo "curl $SERVICE_URL/health"
        echo ""
        echo "# Test with MCP Inspector:"
        echo "npx @modelcontextprotocol/inspector $SERVICE_URL/sse"
        echo ""
        
        # Show recent logs
        print_status "Recent logs:"
        gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME" --limit=10 --format="table(timestamp,textPayload)"
        
    else
        print_error "Build failed with status: $BUILD_STATUS"
        print_error "Analyzing build failure..."
        
        # Get detailed build information
        print_status "Build details:"
        gcloud builds describe $BUILD_ID --format="table(status,statusDetail,createTime,finishTime,timing.BUILD.startTime,timing.BUILD.endTime)"
        
        # Get the last few lines of build logs for quick diagnosis
        print_status "Recent build logs (last 50 lines):"
        echo "----------------------------------------"
        gcloud builds log $BUILD_ID --limit=50 | tail -n 50
        echo "----------------------------------------"
        
        # Get failure reasons from build steps
        print_status "Build step statuses:"
        gcloud builds describe $BUILD_ID --format="table(steps[].name,steps[].status,steps[].timing.startTime,steps[].timing.endTime)" 2>/dev/null
        
        print_error "Build Console URL: https://console.cloud.google.com/cloud-build/builds/$BUILD_ID?project=$PROJECT_ID"
        print_error ""
        print_error "Common failure reasons:"
        print_error "  1. Missing or invalid Artifact Registry repository"
        print_error "  2. Insufficient permissions for Cloud Build service account"
        print_error "  3. Invalid substitution values in cloudbuild.yaml"
        print_error "  4. Docker build failures (check Dockerfile)"
        print_error "  5. Cloud Run deployment issues (region, service name conflicts)"
        print_error ""
        print_error "To debug further:"
        print_error "  - Check the full logs: gcloud builds log $BUILD_ID"
        print_error "  - Verify Artifact Registry repo exists: gcloud artifacts repositories list --location=$GOOGLE_CLOUD_LOCATION"
        print_error "  - Check Cloud Build service account permissions"
        
        exit 1
    fi
else
    print_error "Failed to submit build to Cloud Build."
    print_error "Build submission exit code: $BUILD_SUBMIT_EXIT_CODE"
    
    # Check if we got a valid build ID despite errors
    if [[ "$BUILD_ID" =~ ^[a-f0-9-]{36}$ ]]; then
        print_warning "Got build ID despite submission error: $BUILD_ID"
        print_status "You can monitor this build at:"
        echo "https://console.cloud.google.com/cloud-build/builds/$BUILD_ID?project=$PROJECT_ID"
    else
        print_error "No valid build ID received."
    fi
    
    print_error "Full error output:"
    echo "----------------------------------------"
    echo "$BUILD_OUTPUT"
    echo "----------------------------------------"
    
    print_error "Common submission failure reasons:"
    print_error "  1. gcloud not authenticated - run: gcloud auth login"
    print_error "  2. Project not set or invalid - check: gcloud config get-value project"
    print_error "  3. Cloud Build API not enabled - enable at: https://console.cloud.google.com/flows/enableapi?apiid=cloudbuild.googleapis.com&project=$PROJECT_ID"
    print_error "  4. Insufficient permissions for Cloud Build"
    print_error "  5. Invalid cloudbuild.yaml syntax"
    print_error "  6. Missing or invalid substitution values"
    print_error ""
    print_error "Environment variables used:"
    print_error "  PROJECT_ID=$PROJECT_ID"
    print_error "  GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT"
    print_error "  GOOGLE_CLOUD_LOCATION=$GOOGLE_CLOUD_LOCATION"
    print_error "  ENVIRONMENT=$ENVIRONMENT"
    print_error ""
    print_error "To debug further:"
    print_error "  - Verify gcloud auth: gcloud auth list"
    print_error "  - Check project access: gcloud projects describe $PROJECT_ID"
    print_error "  - Validate cloudbuild.yaml: gcloud builds submit --config cloudbuild.yaml --dry-run"
    
    exit 1
fi

print_success "Deployment script completed!"