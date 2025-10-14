#!/bin/bash

# Advanced Deploy script for ServiceNow MCP Server to Google Cloud Run
# This script provides more options and checks for deployment

set -e  # Exit on any error

# Default values
REGION="europe-southwest1"
SERVICE_NAME="servicenow-mcp"
ARTIFACT_REGISTRY="hoopie-agents"
FOLLOW_LOGS=true
SKIP_TESTS=false
TIMEOUT=300

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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

print_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -r, --region REGION          Set the deployment region (default: $REGION)"
    echo "  -s, --service SERVICE        Set the service name (default: $SERVICE_NAME)"
    echo "  -a, --artifact-registry REG  Set the artifact registry (default: $ARTIFACT_REGISTRY)"
    echo "  -t, --timeout SECONDS        Build timeout in seconds (default: $TIMEOUT)"
    echo "  --no-logs                    Don't follow build logs"
    echo "  --skip-tests                 Skip post-deployment tests"
    echo "  --check-secrets              Check if secrets are properly configured"
    echo "  -h, --help                   Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                           # Deploy with default settings"
    echo "  $0 --region us-central1      # Deploy to us-central1"
    echo "  $0 --skip-tests --no-logs    # Quick deployment without tests or logs"
    echo "  $0 --check-secrets           # Check secrets configuration"
}

# Function to check prerequisites
check_prerequisites() {
    print_step "Checking prerequisites..."
    
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
    
    # Get current project
    PROJECT_ID=$(gcloud config get-value project)
    if [ -z "$PROJECT_ID" ]; then
        print_error "No project is set. Please run 'gcloud config set project PROJECT_ID' first."
        exit 1
    fi
    
    # Check if cloudbuild.yaml exists
    if [ ! -f "cloudbuild.yaml" ]; then
        print_error "cloudbuild.yaml not found. Make sure you're in the correct directory."
        exit 1
    fi
    
    # Check if required APIs are enabled
    print_status "Checking required APIs..."
    required_apis=("cloudbuild.googleapis.com" "run.googleapis.com" "secretmanager.googleapis.com")
    
    for api in "${required_apis[@]}"; do
        if ! gcloud services list --enabled --filter="name:$api" --format="value(name)" | grep -q "$api"; then
            print_warning "API $api is not enabled. Enabling now..."
            gcloud services enable "$api"
        fi
    done
    
    print_success "Prerequisites check completed!"
}

# Function to check secrets
check_secrets() {
    print_step "Checking secrets configuration..."
    
    required_secrets=("servicenow-instance-url" "servicenow-username" "servicenow-password" "mcp-bearer-token")
    
    for secret in "${required_secrets[@]}"; do
        if gcloud secrets describe "$secret" --format="value(name)" &> /dev/null; then
            print_success "Secret $secret exists"
        else
            print_error "Secret $secret does not exist. Please create it first."
            echo "Example: gcloud secrets create $secret --data-file=- <<< 'your-secret-value'"
        fi
    done
}

# Function to run post-deployment tests
run_tests() {
    print_step "Running post-deployment tests..."
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)")
    
    if [ -z "$SERVICE_URL" ]; then
        print_error "Could not get service URL"
        return 1
    fi
    
    print_status "Testing service at: $SERVICE_URL"
    
    # Test health endpoint
    print_status "Testing health endpoint..."
    if curl -s -f "$SERVICE_URL/health" > /dev/null; then
        print_success "Health check passed"
    else
        print_error "Health check failed"
        return 1
    fi
    
    # Test SSE endpoint (just check if it responds)
    print_status "Testing SSE endpoint..."
    if curl -s -f "$SERVICE_URL/sse" -H "Accept: text/event-stream" --max-time 5 > /dev/null; then
        print_success "SSE endpoint accessible"
    else
        print_warning "SSE endpoint test inconclusive (this might be normal)"
    fi
    
    print_success "Post-deployment tests completed!"
}

# Function to show deployment summary
show_summary() {
    print_step "Deployment Summary"
    echo "================================"
    echo "Project ID: $PROJECT_ID"
    echo "Service Name: $SERVICE_NAME"
    echo "Region: $REGION"
    echo "Artifact Registry: $ARTIFACT_REGISTRY"
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)" 2>/dev/null || echo "Not available")
    echo "Service URL: $SERVICE_URL"
    
    echo ""
    echo "Useful commands:"
    echo "  View logs: gcloud logs read 'resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME' --limit=50"
    echo "  Test health: curl $SERVICE_URL/health"
    echo "  MCP Inspector: npx @modelcontextprotocol/inspector $SERVICE_URL/sse"
    echo "  Update secrets: gcloud secrets versions add SECRET_NAME --data-file=-"
    echo "  Redeploy: $0"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        -s|--service)
            SERVICE_NAME="$2"
            shift 2
            ;;
        -a|--artifact-registry)
            ARTIFACT_REGISTRY="$2"
            shift 2
            ;;
        -t|--timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --no-logs)
            FOLLOW_LOGS=false
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --check-secrets)
            check_prerequisites
            check_secrets
            exit 0
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main deployment process
main() {
    print_status "Starting ServiceNow MCP Server deployment..."
    echo "========================================"
    
    # Check prerequisites
    check_prerequisites
    
    print_status "Deployment Configuration:"
    echo "  Project: $PROJECT_ID"
    echo "  Service: $SERVICE_NAME"
    echo "  Region: $REGION"
    echo "  Artifact Registry: $ARTIFACT_REGISTRY"
    echo "  Timeout: ${TIMEOUT}s"
    echo ""
    
    # Submit the build
    print_step "Submitting build to Cloud Build..."
    
    if [ "$FOLLOW_LOGS" = true ]; then
        # Submit build and follow logs
        gcloud builds submit --config cloudbuild.yaml --timeout="${TIMEOUT}s"
        BUILD_SUCCESS=$?
    else
        # Submit build without following logs
        BUILD_OUTPUT=$(gcloud builds submit --config cloudbuild.yaml --timeout="${TIMEOUT}s" --format="value(id)" 2>&1)
        BUILD_ID=$(echo "$BUILD_OUTPUT" | tail -n 1)
        BUILD_SUCCESS=$?
        
        if [ $BUILD_SUCCESS -eq 0 ]; then
            print_status "Build submitted with ID: $BUILD_ID"
            print_status "Monitor at: https://console.cloud.google.com/cloud-build/builds/$BUILD_ID?project=$PROJECT_ID"
        fi
    fi
    
    # Check build result
    if [ $BUILD_SUCCESS -eq 0 ]; then
        print_success "Build and deployment completed successfully!"
        
        # Run tests if not skipped
        if [ "$SKIP_TESTS" = false ]; then
            run_tests
        fi
        
        # Show summary
        show_summary
        
    else
        print_error "Build failed!"
        print_error "Check the build logs above for more details."
        exit 1
    fi
}

# Run main function
main

print_success "Deployment script completed!"