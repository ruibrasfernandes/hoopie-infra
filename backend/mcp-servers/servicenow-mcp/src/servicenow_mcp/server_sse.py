"""
ServiceNow MCP Server

This module provides the main implementation of the ServiceNow MCP server.
"""

import argparse
import os
from typing import Dict, Union

import uvicorn
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from starlette.middleware.base import BaseHTTPMiddleware

from servicenow_mcp.server import ServiceNowMCP
from servicenow_mcp.utils.config import AuthConfig, AuthType, BasicAuthConfig, ServerConfig


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware to handle Bearer token authentication."""
    
    def __init__(self, app, bearer_token: str):
        super().__init__(app)
        self.bearer_token = bearer_token
    
    async def dispatch(self, request: Request, call_next):
        # Skip authentication for health checks
        if request.url.path in ["/health", "/", "/favicon.ico"]:
            return await call_next(request)
        
        # Check Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(
                {"error": "Missing Authorization header"}, 
                status_code=401
            )
        
        # Validate Bearer token
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                {"error": "Invalid Authorization header format. Expected 'Bearer <token>'"}, 
                status_code=401
            )
        
        token = auth_header[7:]  # Remove "Bearer " prefix
        if token != self.bearer_token:
            return JSONResponse(
                {"error": "Invalid Bearer token"}, 
                status_code=401
            )
        
        # Token is valid, continue with request
        return await call_next(request)


def create_starlette_app(mcp_server: Server, bearer_token: str = None, *, debug: bool = False) -> Starlette:
    """Create a Starlette application that can serve the provided mcp server with SSE."""
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> None:
        async with sse.connect_sse(
            request.scope,
            request.receive,
            request._send,  # noqa: SLF001
        ) as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )

    app = Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )
    
    # Add authentication middleware if bearer token is provided
    if bearer_token:
        app.add_middleware(AuthenticationMiddleware, bearer_token=bearer_token)
    
    return app


class ServiceNowSSEMCP(ServiceNowMCP):
    """
    ServiceNow MCP Server implementation.

    This class provides a Model Context Protocol (MCP) server for ServiceNow,
    allowing LLMs to interact with ServiceNow data and functionality.
    """

    def __init__(self, config: Union[Dict, ServerConfig]):
        """
        Initialize the ServiceNow MCP server.

        Args:
            config: Server configuration, either as a dictionary or ServerConfig object.
        """
        super().__init__(config)

    def start(self, host: str = "0.0.0.0", port: int = 8080):
        """
        Start the MCP server with SSE transport using Starlette and Uvicorn.

        Args:
            host: Host address to bind to
            port: Port to listen on
        """
        # Get bearer token from environment
        bearer_token = os.getenv("MCP_BEARER_TOKEN")
        
        # Create Starlette app with SSE transport and authentication
        starlette_app = create_starlette_app(self.mcp_server, bearer_token=bearer_token, debug=True)

        # Run using uvicorn
        uvicorn.run(starlette_app, host=host, port=port)


def create_servicenow_mcp(instance_url: str, username: str, password: str):
    """
    Create a ServiceNow MCP server with minimal configuration.

    This is a simplified factory function that creates a pre-configured
    ServiceNow MCP server with basic authentication.

    Args:
        instance_url: ServiceNow instance URL
        username: ServiceNow username
        password: ServiceNow password

    Returns:
        A configured ServiceNowMCP instance ready to use

    Example:
        ```python
        from servicenow_mcp.server import create_servicenow_mcp

        # Create an MCP server for ServiceNow
        mcp = create_servicenow_mcp(
            instance_url="https://instance.service-now.com",
            username="admin",
            password="password"
        )

        # Start the server
        mcp.start()
        ```
    """

    # Create basic auth config
    auth_config = AuthConfig(
        type=AuthType.BASIC, basic=BasicAuthConfig(username=username, password=password)
    )

    # Create server config
    config = ServerConfig(instance_url=instance_url, auth=auth_config)

    # Create and return server
    return ServiceNowSSEMCP(config)


def main():
    import logging
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    logger.info("=== SERVICENOW MCP SERVER STARTING ===")
    
    load_dotenv()
    logger.info("Environment loaded")

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run ServiceNow MCP SSE-based server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on")
    args = parser.parse_args()
    logger.info(f"Args parsed: host={args.host}, port={args.port}")

    # Get all environment variables
    instance_url = os.getenv("SERVICENOW_INSTANCE_URL")
    username = os.getenv("SERVICENOW_USERNAME") 
    password = os.getenv("SERVICENOW_PASSWORD")
    tool_package = os.getenv("MCP_TOOL_PACKAGE", "full")
    bearer_token = os.getenv("MCP_BEARER_TOKEN")
    
    logger.info("=== ENVIRONMENT VARIABLES ===")
    logger.info(f"ServiceNow Instance URL: {instance_url}")
    logger.info(f"ServiceNow Username: {username}")
    logger.info(f"ServiceNow Password: {'*' * len(password) if password else 'None'}")
    logger.info(f"MCP Tool Package: {tool_package}")
    logger.info(f"MCP Bearer Token: {'*' * len(bearer_token) if bearer_token else 'None'}")
    logger.info(f"Authentication: {'ENABLED' if bearer_token else 'DISABLED'}")
    logger.info("=== END ENVIRONMENT VARIABLES ===")
    
    if not instance_url or not username or not password:
        logger.error("Missing required environment variables!")
        logger.error(f"SERVICENOW_INSTANCE_URL: {'SET' if instance_url else 'MISSING'}")
        logger.error(f"SERVICENOW_USERNAME: {'SET' if username else 'MISSING'}")
        logger.error(f"SERVICENOW_PASSWORD: {'SET' if password else 'MISSING'}")
        return
    
    logger.info("Creating ServiceNow MCP server...")
    try:
        server = create_servicenow_mcp(
            instance_url=instance_url,
            username=username,
            password=password,
        )
        logger.info("Server created successfully")
    except Exception as e:
        logger.error(f"Failed to create server: {e}", exc_info=True)
        return
        
    logger.info("Starting server...")
    try:
        server.start(host=args.host, port=args.port)
    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)


if __name__ == "__main__":
    main()
