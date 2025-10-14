#!/bin/bash

# Deploy script for Hoopie API Endpoints
# Usage: ./deploy.sh [dev|stag|prod]
# Examples:
#   ./deploy.sh          # Deploys to dev (default)
#   ./deploy.sh dev      # Deploys to dev
#   ./deploy.sh stag     # Deploys to staging
#   ./deploy.sh prod     # Deploys to production

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT=${1:-dev}
REGION="europe-southwest1"

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|stag|prod)$ ]]; then
  echo -e "${RED}Error: Invalid environment '$ENVIRONMENT'${NC}"
  echo "Usage: $0 [dev|stag|prod]"
  exit 1
fi

# Check if current branch matches deployment environment
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
EXPECTED_BRANCH=$ENVIRONMENT

# Map main branch to prod environment
if [ "$ENVIRONMENT" = "prod" ]; then
  EXPECTED_BRANCH="main"
fi

if [ "$CURRENT_BRANCH" != "$EXPECTED_BRANCH" ]; then
  echo -e "${RED}========================================${NC}"
  echo -e "${RED}❌ Branch Mismatch Error${NC}"
  echo -e "${RED}========================================${NC}"
  echo -e "Current branch:  ${YELLOW}$CURRENT_BRANCH${NC}"
  echo -e "Expected branch: ${YELLOW}$EXPECTED_BRANCH${NC}"
  echo -e "Target environment: ${YELLOW}$ENVIRONMENT${NC}"
  echo ""
  echo -e "${YELLOW}To deploy to $ENVIRONMENT, you must be on the $EXPECTED_BRANCH branch.${NC}"
  echo -e "Run: ${GREEN}git checkout $EXPECTED_BRANCH${NC}"
  echo -e "${RED}========================================${NC}"
  exit 1
fi

# Map environment to project
case $ENVIRONMENT in
  dev)
    PROJECT_ID="hoopie-dev"
    ;;
  stag)
    PROJECT_ID="hoopie-stag"
    ;;
  prod)
    PROJECT_ID="hoopie-prod"
    ;;
esac

# Cloud Build config file
CONFIG_FILE="deploy/cloudbuild-api-endpoints.yaml"

# Display deployment info
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Hoopie API Endpoints Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Environment: ${YELLOW}$ENVIRONMENT${NC}"
echo -e "Project:     ${YELLOW}$PROJECT_ID${NC}"
echo -e "Region:      ${YELLOW}$REGION${NC}"
echo -e "Config:      ${YELLOW}$CONFIG_FILE${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
  echo -e "${RED}Error: Config file '$CONFIG_FILE' not found${NC}"
  exit 1
fi

# Confirm deployment for prod
if [ "$ENVIRONMENT" = "prod" ]; then
  echo -e "${YELLOW}⚠️  WARNING: You are about to deploy to PRODUCTION!${NC}"
  read -p "Are you sure you want to continue? (yes/no): " -r
  echo
  if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo -e "${RED}Deployment cancelled${NC}"
    exit 1
  fi
fi

# Set gcloud project
echo -e "${GREEN}Setting gcloud project...${NC}"
gcloud config set project "$PROJECT_ID"

# Submit build
echo ""
echo -e "${GREEN}Submitting Cloud Build...${NC}"
gcloud builds submit \
  --config="$CONFIG_FILE" \
  --substitutions="_ENVIRONMENT=$ENVIRONMENT,_REGION=$REGION" \
  --project="$PROJECT_ID"

# Check if build succeeded
if [ $? -eq 0 ]; then
  echo ""
  echo -e "${GREEN}========================================${NC}"
  echo -e "${GREEN}✅ Deployment successful!${NC}"
  echo -e "${GREEN}========================================${NC}"
  echo -e "Environment: ${YELLOW}$ENVIRONMENT${NC}"
  echo -e "Project:     ${YELLOW}$PROJECT_ID${NC}"
  echo -e "${GREEN}========================================${NC}"
else
  echo ""
  echo -e "${RED}========================================${NC}"
  echo -e "${RED}❌ Deployment failed!${NC}"
  echo -e "${RED}========================================${NC}"
  exit 1
fi
