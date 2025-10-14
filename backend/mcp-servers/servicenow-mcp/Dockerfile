FROM python:3.11-slim

WORKDIR /app

# Copy project files from the ServiceNow MCP directory
COPY backend/mcp-servers/servicenow-mcp/pyproject.toml backend/mcp-servers/servicenow-mcp/README.md backend/mcp-servers/servicenow-mcp/LICENSE ./
COPY backend/mcp-servers/servicenow-mcp/src/ ./src/
COPY backend/mcp-servers/servicenow-mcp/config/ ./config/

# Install the package in development mode
RUN pip install -e .

# Expose the port the app runs on
EXPOSE 8080

# Command to run the application using the provided CLI
CMD ["servicenow-mcp-sse", "--host=0.0.0.0", "--port=8080"] 