#!/bin/bash

echo "Testing API Endpoints ignore file contents..."

# Change to project root directory
cd ../../

# Create a test archive to see what's included
tar --exclude-from=.gcloudignore-api-endpoints -czf /tmp/test-api-endpoints.tgz . 2>/dev/null

echo "Files included in API Endpoints deployment:"
tar -tzf /tmp/test-api-endpoints.tgz | grep -E "(backend/end-points|deploy/terraform/api-endpoints|deploy/cloudbuild)" | head -20

echo
echo "Checking if essential files exist:"
tar -tzf /tmp/test-api-endpoints.tgz | grep "Dockerfile" || echo "No Dockerfile found!"
tar -tzf /tmp/test-api-endpoints.tgz | grep "agent_call.py" || echo "No agent_call.py found!"
tar -tzf /tmp/test-api-endpoints.tgz | grep "deploy/cloudbuild-api-endpoints.yaml" || echo "No deploy/cloudbuild-api-endpoints.yaml found!"

echo
echo "Archive size:"
ls -lh /tmp/test-api-endpoints.tgz | awk '{print $5}'

echo
echo "Excluded directories check (should be empty):"
tar -tzf /tmp/test-api-endpoints.tgz | grep -E "(hoopie-adk/|hoopie-web/|backend/mcp-servers/)" | head -5 || echo "✅ Large directories properly excluded"

# Cleanup
rm /tmp/test-api-endpoints.tgz