#!/bin/bash

# Firebase Web Configuration Helper
# This script explains why Firebase config doesn't need Secret Manager
# and provides utilities for managing Firebase app configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_status() {
    echo -e "${YELLOW}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

show_firebase_info() {
    echo -e "${BLUE}🔥 Firebase Configuration Information${NC}"
    echo ""
    echo "Firebase client configuration is NOT secret and should NOT be stored in Secret Manager because:"
    echo "• API keys are public and meant to be embedded in client-side code"
    echo "• Configuration is sent to browsers and visible in network requests"
    echo "• Security is handled by Firebase security rules, not by hiding config"
    echo "• The deployment script now auto-generates config from project metadata"
    echo ""
}

# Function to display current Firebase configuration for an environment
show_firebase_config() {
    local env=$1
    
    # Map environment to project
    local project_id
    case $env in
        dev)
            project_id="hoopie-dev"
            ;;
        stag)
            project_id="hoopie-stag"
            ;;
        demo)
            project_id="hoopie-demo"
            ;;
        prod)
            project_id="hoopie-prod"
            ;;
        *)
            print_error "Invalid environment: $env"
            return 1
            ;;
    esac
    
    print_status "Firebase configuration for $env environment (project: $project_id):"
    
    # Try to get Firebase app configuration
    if firebase apps:list --project="$project_id" &>/dev/null; then
        echo ""
        firebase apps:list --project="$project_id"
        echo ""
        
        # Try to get SDK config
        if firebase apps:sdkconfig web --project="$project_id" &>/dev/null; then
            print_status "Firebase SDK configuration:"
            firebase apps:sdkconfig web --project="$project_id"
        fi
    else
        print_error "Cannot access Firebase project $project_id"
        print_error "Make sure you're authenticated: firebase login"
    fi
}

# Function to verify deployment readiness
verify_deployment() {
    local env=$1
    
    print_status "Verifying deployment readiness for $env..."
    
    # Check Firebase authentication
    if ! firebase projects:list &>/dev/null; then
        print_error "Not authenticated with Firebase. Run: firebase login"
        return 1
    fi
    
    # Check if environment project exists
    local project_id="hoopie-$env"
    if firebase projects:list | grep -q "$project_id"; then
        print_success "Firebase project $project_id is accessible"
    else
        print_error "Firebase project $project_id not found or not accessible"
        return 1
    fi
    
    print_success "Deployment verification passed for $env"
}

# Main execution
case "${1:-help}" in
    "info")
        show_firebase_info
        ;;
    "config")
        if [ -z "$2" ]; then
            print_error "Usage: $0 config <environment>"
            exit 1
        fi
        show_firebase_config "$2"
        ;;
    "verify")
        if [ -z "$2" ]; then
            print_error "Usage: $0 verify <environment>"
            exit 1
        fi
        verify_deployment "$2"
        ;;
    "help"|*)
        show_firebase_info
        echo -e "${YELLOW}Usage:${NC}"
        echo "  $0 info                    - Show Firebase configuration information"
        echo "  $0 config <env>           - Show Firebase config for environment"
        echo "  $0 verify <env>           - Verify deployment readiness"
        echo ""
        echo -e "${YELLOW}Examples:${NC}"
        echo "  $0 config dev             - Show dev environment Firebase config"
        echo "  $0 verify prod            - Verify prod deployment readiness"
        ;;
esac