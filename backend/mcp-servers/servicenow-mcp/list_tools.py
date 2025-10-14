#!/usr/bin/env python3
"""
Simple script to list all available tools from the ServiceNow MCP server.
"""

import asyncio
import json
from dotenv import load_dotenv
from servicenow_mcp.server import ServiceNowMCP
from servicenow_mcp.utils.config import ServerConfig, AuthConfig, AuthType, BasicAuthConfig
import os

async def list_tools():
    """List all available tools from the ServiceNow MCP server."""
    # Load environment variables
    load_dotenv()
    
    # Create basic config (you can modify this based on your auth method)
    config = ServerConfig(
        instance_url=os.getenv("SERVICENOW_INSTANCE_URL", "https://example.service-now.com"),
        auth=AuthConfig(
            type=AuthType.BASIC,
            basic=BasicAuthConfig(
                username=os.getenv("SERVICENOW_USERNAME", "admin"),
                password=os.getenv("SERVICENOW_PASSWORD", "password")
            )
        ),
        debug=True
    )
    
    # Create MCP server instance
    mcp_server = ServiceNowMCP(config)
    
    # Get tools list
    tools = await mcp_server._list_tools_impl()
    
    print(f"\n🔧 Available Tools ({len(tools)} total):\n")
    print("=" * 60)
    
    for i, tool in enumerate(tools, 1):
        print(f"{i:2d}. {tool.name}")
        print(f"    Description: {tool.description}")
        print()
    
    # Also output as JSON for programmatic use
    tools_json = [
        {
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.inputSchema
        }
        for tool in tools
    ]
    
    with open("tools_list.json", "w") as f:
        json.dump(tools_json, f, indent=2)
    
    print(f"📄 Full tool details saved to: tools_list.json")

if __name__ == "__main__":
    asyncio.run(list_tools())