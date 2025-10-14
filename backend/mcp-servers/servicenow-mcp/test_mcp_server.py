#!/usr/bin/env python3
"""
Test script to check if get_incident is available in the deployed MCP server.
"""
import asyncio
import json
import sys
from mcp import ClientSession
from mcp.client.sse import sse_client

async def test_mcp_server():
    """Test the MCP server to check if get_incident is available."""
    server_url = "https://servicenow-mcp-zknwd5e32a-no.a.run.app/sse"
    
    print(f"Testing MCP server at: {server_url}")
    print("=" * 50)
    
    try:
        # Create SSE client
        transport = sse_client(server_url)
        
        async with ClientSession(transport) as session:
            # Initialize the connection
            await session.initialize()
            print("✅ Connected to MCP server")
            
            # List available tools
            tools = await session.list_tools()
            print(f"✅ Found {len(tools)} tools")
            
            # Check if get_incident is available
            tool_names = [tool.name for tool in tools]
            
            if "get_incident" in tool_names:
                print("✅ get_incident is available!")
                
                # Find the get_incident tool
                get_incident_tool = next(tool for tool in tools if tool.name == "get_incident")
                print(f"   Description: {get_incident_tool.description}")
                print(f"   Input Schema: {json.dumps(get_incident_tool.inputSchema, indent=2)}")
                
            else:
                print("❌ get_incident is NOT available")
                print("Available tools:")
                for tool_name in sorted(tool_names):
                    print(f"   - {tool_name}")
                
    except Exception as e:
        print(f"❌ Error testing MCP server: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_server())