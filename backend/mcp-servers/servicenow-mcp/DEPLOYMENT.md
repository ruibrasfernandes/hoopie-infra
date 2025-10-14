# ServiceNow MCP Server Deployment Guide

This guide explains how to deploy the ServiceNow MCP Server to Google Cloud Run using the provided deployment scripts.

## Prerequisites

1. **Google Cloud SDK**: Install and configure the gcloud CLI
2. **Authentication**: Run `gcloud auth login`
3. **Project**: Set your project with `gcloud config set project PROJECT_ID`
4. **APIs**: The following APIs will be automatically enabled:
   - Cloud Build API
   - Cloud Run API  
   - Secret Manager API

## Deployment Scripts

### 1. Quick Deploy (`quick-deploy.sh`)

The simplest way to deploy with minimal output:

```bash
./quick-deploy.sh
```

**Features:**
- One-click deployment
- Minimal output
- Basic error checking
- Shows service URL after deployment

### 2. Standard Deploy (`deploy.sh`)

Standard deployment with detailed output and logging:

```bash
./deploy.sh
```

**Features:**
- Detailed progress information
- Follows build logs in real-time
- Shows service URL and test commands
- Displays recent logs after deployment

### 3. Advanced Deploy (`deploy-advanced.sh`)

Full-featured deployment script with advanced options:

```bash
./deploy-advanced.sh [OPTIONS]
```

**Options:**
- `-r, --region REGION`: Set deployment region (default: europe-southwest1)
- `-s, --service SERVICE`: Set service name (default: servicenow-mcp)
- `-a, --artifact-registry REG`: Set artifact registry (default: hoopie-agents)
- `-t, --timeout SECONDS`: Build timeout (default: 300)
- `--no-logs`: Don't follow build logs
- `--skip-tests`: Skip post-deployment tests
- `--check-secrets`: Check if secrets are properly configured
- `-h, --help`: Show help message

**Examples:**
```bash
# Deploy with default settings
./deploy-advanced.sh

# Deploy to different region
./deploy-advanced.sh --region us-central1

# Quick deployment without tests or logs
./deploy-advanced.sh --skip-tests --no-logs

# Check secrets configuration
./deploy-advanced.sh --check-secrets
```

## Required Secrets

Before deploying, ensure these secrets are created in Google Secret Manager:

```bash
# ServiceNow instance URL
gcloud secrets create servicenow-instance-url --data-file=- <<< 'https://your-instance.service-now.com'

# ServiceNow username
gcloud secrets create servicenow-username --data-file=- <<< 'your-username'

# ServiceNow password
gcloud secrets create servicenow-password --data-file=- <<< 'your-password'

# MCP Bearer token for authentication
gcloud secrets create mcp-bearer-token --data-file=- <<< 'your-bearer-token'
```

## Testing Deployment

After deployment, test your service:

```bash
# Test health endpoint
curl https://your-service-url/health

# Test with MCP Inspector
npx @modelcontextprotocol/inspector https://your-service-url/sse
```

## Monitoring

### View Logs
```bash
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=servicenow-mcp" --limit=50
```

### Check Service Status
```bash
gcloud run services describe servicenow-mcp --region=europe-southwest1
```

### Update Secrets
```bash
gcloud secrets versions add SECRET_NAME --data-file=- <<< 'new-value'
```

## Troubleshooting

### Common Issues

1. **Build fails**: Check that your project has the necessary APIs enabled
2. **Service doesn't start**: Verify all secrets are properly configured
3. **Authentication errors**: Ensure the bearer token is correctly set
4. **ServiceNow connection fails**: Check instance URL, username, and password

### Debug Commands

```bash
# Check build history
gcloud builds list --limit=10

# View specific build logs
gcloud builds log BUILD_ID

# Check service configuration
gcloud run services describe servicenow-mcp --region=europe-southwest1

# Test service locally (if needed)
docker build -t servicenow-mcp .
docker run -p 8080:8080 servicenow-mcp
```

## Configuration

The deployment uses the following configuration:

- **Region**: europe-southwest1
- **Memory**: 1Gi
- **CPU**: 1
- **Max Instances**: 10
- **Port**: 8080
- **Timeout**: 900s (15 minutes)

To modify these settings, edit the `cloudbuild.yaml` file.

## Schema Compatibility

The deployment includes fixes for Vertex AI schema compatibility:
- Removed `Optional[type]` with non-None defaults to prevent `any_of` schema generation
- All tools now work correctly with Google ADK/Vertex AI

## Security

- All credentials are stored in Google Secret Manager
- Bearer token authentication is required for API access
- Health check endpoints are accessible without authentication
- Service runs with minimal required permissions