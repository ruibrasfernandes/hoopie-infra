# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Hoopie-infra is the infrastructure repository for the Hoopie project, which consists of:
- **Backend API endpoints**: FastAPI services deployed on Google Cloud Run
- **MCP servers**: Model Context Protocol servers for ServiceNow and Pandoc integrations
- **Deployment infrastructure**: Terraform configurations for multi-environment GCP deployments

## Environment Configuration

The project uses `.env` files for configuration. Key environment variables:
```
GOOGLE_CLOUD_PROJECT=hoopie-dev
GOOGLE_CLOUD_LOCATION=europe-southwest1
```

Environments: `dev`, `stag` (staging), `prod` (production)

## High-Level Architecture

### 1. Backend API Endpoints (`backend/end-points/`)
- **agent_call.py**: Main FastAPI service that proxies requests to Vertex AI Agent Engine
  - Manages user sessions (in-memory, mapped by Firebase UID)
  - Discovers and caches the latest agent at startup via `discover_latest_agent()`
  - Provides `/query`, `/clear-session`, `/health` endpoints
  - Integrates Firebase authentication via `security/ui_firebase.py`
  - Deployed to Cloud Run via `deploy/cloudbuild-api-endpoints.yaml`

- **streaming_agent.py**: WebSocket-based streaming agent service for voice/audio interactions
  - Uses Google ADK (Agent Development Kit) with `InMemoryRunner`
  - Bidirectional WebSocket communication at `/ws/{user_id}?is_audio=<bool>`
  - Supports both text and audio (PCM) modalities
  - Imports agent from external `hoopie-adk` repository

### 2. MCP Servers (`backend/mcp-servers/`)
- **servicenow-mcp**: Comprehensive ServiceNow integration
  - Provides 50+ tools for incident management, catalog operations, change management, workflows, knowledge base, user management, agile tools
  - Supports tool packaging (role-based subsets) via `MCP_TOOL_PACKAGE` env var
  - Deployable as stdio or SSE (Server-Sent Events) server
  - Authentication: Basic, OAuth, or API Key
  - Deployed to Cloud Run via `deploy/cloudbuild-servicenow-mcp.yaml`

- **mcp-pandoc**: Document conversion MCP server using Pandoc

### 3. Firebase Scripts (`backend/scripts/`)
Utility scripts for Firebase user management and testing.

### 4. Infrastructure as Code (`deploy/terraform/`)
Organized by service and environment:
```
deploy/terraform/
├── api-endpoints/environments/{dev,stag,prod}/  # Cloud Run for API endpoints
├── servicenow-mcp/environments/{dev,stag,prod}/ # Cloud Run for ServiceNow MCP
├── modules/                                      # Reusable Terraform modules
│   ├── cloud_run/
│   ├── service_accounts/
│   ├── artifact_registry/
│   ├── vertex_ai/
│   └── state_bucket/
└── environments/{dev,stag,prod}/                # Base infrastructure per environment
```

Each environment has `main.tf`, `variables.tf`, and `outputs.tf`. The root `main.tf` defines Terraform providers.

### 5. CI/CD (`deploy/`)
Cloud Build configurations for automated deployments:
- **cloudbuild-api-endpoints.yaml**: Builds Docker image, pushes to Artifact Registry, runs Terraform for Cloud Run
- **cloudbuild-servicenow-mcp.yaml**: Similar flow for ServiceNow MCP server
- **cloudbuild-hoopie-sdm.yaml**: (Exists but details not analyzed)
- **cloudbuild-infra.yaml**: Infrastructure-only deployments

Uses dedicated service account: `hoopie-cloudbuild-{environment}@{project}.iam.gserviceaccount.com`

## Common Development Commands

### Python Environment
This project uses `uv` for Python dependency management:
```bash
# The project requires Python 3.13+
uv sync            # Install dependencies
uv run <script>    # Run a script with dependencies
```

### Running Services Locally

**API Endpoints:**
```bash
cd backend/end-points
uv run uvicorn agent_call:app --reload --port 8080
```

**Streaming Agent:**
```bash
cd backend/end-points
uv run uvicorn streaming_agent:app --reload --port 8080
```

**ServiceNow MCP (stdio mode):**
```bash
cd backend/mcp-servers/servicenow-mcp
uv run python -m servicenow_mcp.cli
```

**ServiceNow MCP (SSE mode):**
```bash
cd backend/mcp-servers/servicenow-mcp
uv run servicenow-mcp-sse --instance-url=<url> --username=<user> --password=<pass>
```

**ServiceNow MCP Inspector (for testing):**
```bash
cd backend/mcp-servers/servicenow-mcp
npx @modelcontextprotocol/inspector uv run python -m servicenow_mcp.cli
```

### Testing

**ServiceNow MCP:**
```bash
cd backend/mcp-servers/servicenow-mcp
uv run pytest                    # Run all tests
uv run pytest tests/test_<name>  # Run specific test file
```

### Deployment

**Deploy API Endpoints:**
```bash
gcloud builds submit --config=deploy/cloudbuild-api-endpoints.yaml \
  --substitutions=_ENVIRONMENT=dev,_REGION=europe-southwest1
```

**Deploy ServiceNow MCP:**
```bash
gcloud builds submit --config=deploy/cloudbuild-servicenow-mcp.yaml \
  --substitutions=_ENVIRONMENT=dev,_REGION=europe-southwest1
```

**Terraform Operations:**
```bash
cd deploy/terraform/<service>/environments/<env>
terraform init
terraform plan -var="project_id=hoopie-dev" -var="environment=dev" -var="region=europe-southwest1"
terraform apply
```

## Important Integration Notes

### Agent Discovery Pattern
The `agent_call.py` service discovers agents at startup using:
```python
ae_apps = list(agent_engines.list(filter=f'display_name="{app_name}"'))
# Sorts by creation time to get most recent
```
This is a **one-time lookup** at startup to avoid repeated API calls.

### Session Management
- Sessions are stored in-memory (should be database-backed in production)
- Keyed by Firebase UID (fallback to userId)
- Vertex AI sessions are created lazily on first query if not already created
- Sessions can be cleared via `/clear-session` endpoint

### ServiceNow MCP Tool Packages
To limit tool exposure, set `MCP_TOOL_PACKAGE` to one of:
- `service_desk`, `catalog_builder`, `change_coordinator`, `knowledge_author`
- `platform_developer`, `system_administrator`, `agile_management`
- `full` (default), `none`

Packages are defined in `backend/mcp-servers/servicenow-mcp/config/tool_packages.yaml`.

### Cloud Run Deployment Strategy
All services:
- Build Docker images and push to Artifact Registry
- Use Terraform to provision/update Cloud Run services
- Apply only on `main`/`master` branch or dev/stag environments
- Use dedicated service accounts per environment

## Dependency Management
- Root `pyproject.toml` specifies core dependencies (FastAPI, Vertex AI, etc.)
- Each MCP server has its own `pyproject.toml`
- Use `uv` for all Python operations
