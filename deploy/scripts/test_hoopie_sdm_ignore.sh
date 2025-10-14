#!/bin/bash

echo "Testing Hoopie SDM ignore file contents..."

# Change to project root directory
cd ../../

# Create a test archive to see what's included
tar --exclude-from=.gcloudignore-hoopie-sdm -czf /tmp/test-hoopie-sdm.tgz . 2>/dev/null

echo "Files included in Hoopie SDM deployment:"
tar -tzf /tmp/test-hoopie-sdm.tgz | grep -E "(hoopie-adk|deploy/cloudbuild)" | head -20

echo
echo "Checking if essential files exist:"
tar -tzf /tmp/test-hoopie-sdm.tgz | grep "pyproject.toml" || echo "No pyproject.toml found!"
tar -tzf /tmp/test-hoopie-sdm.tgz | grep "deploy/cloudbuild-hoopie-sdm.yaml" || echo "No deploy/cloudbuild-hoopie-sdm.yaml found!"

echo
echo "Archive size:"
ls -lh /tmp/test-hoopie-sdm.tgz | awk '{print $5}'

echo
echo "Excluded directories check (should be empty):"
tar -tzf /tmp/test-hoopie-sdm.tgz | grep -E "(backend/|deploy/terraform/|hoopie-web/)" | head -5 || echo "✅ Large directories properly excluded"

# Cleanup
rm /tmp/test-hoopie-sdm.tgz