#!/bin/bash

echo "Testing ServiceNow MCP ignore file contents..."

# Change to project root directory
cd ../../

# Create a test archive to see what's included
tar --exclude-from=.gcloudignore-servicenow-mcp -czf /tmp/test-servicenow.tgz . 2>/dev/null

echo "Files included in ServiceNow MCP deployment:"
tar -tzf /tmp/test-servicenow.tgz | grep -E "(backend/mcp-servers/servicenow-mcp|deploy/terraform|deploy/cloudbuild)" | head -20

echo
echo "Checking if Dockerfile exists:"
tar -tzf /tmp/test-servicenow.tgz | grep "Dockerfile" || echo "No Dockerfile found!"

echo
echo "Archive size:"
ls -lh /tmp/test-servicenow.tgz | awk '{print $5}'

# Cleanup
rm /tmp/test-servicenow.tgz