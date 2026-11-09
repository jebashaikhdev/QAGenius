import sys
from pathlib import Path

from mcp import Client, StdioServerParameters

# step 1: build the mcp server and register MCP tools.
# step 2: build mcp client that has function that discovers available tools and a way to call them.
# step 3: Expose these functionalities through FASTAPI Backend(main.py) by adding endpoints.

# This component is responsible for communicating with the MCP server.
# Our implementation uses two important functions. 1. Server configuration 2.Discovering available tools

SERVER_PATH =Path(__file__).with_name("mcp_server.py")

# 1. Server configuration
def get_server_params():
    return StdioServerParameters( # StdioServerParameters configures how the client launches the server.
        command=sys.executable, # sys.executable identifies the Python interpreter running our backend.
        args=[str(SERVER_PATH)] # SERVER_PATH identifies our MCP server file.
    )

# We chose STDIO transport. This means the MCP client launches the MCP server 
# as a subprocess and communicates with it through standard input and standard output.

# 2.Discovering available tools
async def get_mcp_tools():
    async with Client(get_server_params()) as client: # The client launches the MCP server process and establishes communication using STDIO.
        result = await client.list_tools() # The client sends a tools/list request to the MCP server. The server responds with the tools it has registered.
        
        # We then extract their names, descriptions and input schemas.
        # This is important because our AI application doesn't need to hardcode the tool definitions.
        # It can discover them dynamically.
        return [
            {
                "name": tool.name,
                "description": tool.description or "",
                "input_schema": tool.input_schema
            }
            for tool in result.tools
        ]
        
# Following function receives:
# - The name of the tool.
# - The arguments required by that tool.

async def call_mcp_tool(tool_name: str, arguments: dict):
    server_params = get_server_params()
    
    async with Client(server_params) as client:
        result = await client.call_tool( # It sends a tools/call request to the MCP server.
            tool_name,
            arguments
        )
        
        if result.is_error:
            raise RuntimeError(f"MCP Tool failed: {result.content}")
        
        # client extracts the text response and returns it to the caller.
        return "\n".join(
            item.text
            for item in result.content  
            if hasattr(item, "text")
        )

#4. Integrating MCP with FastAPI
# We then exposed MCP functionality through our FastAPI backend.

# We added these endpoints:
# Endpoint	Responsibility
# /api/mcp/get-requirements	Test requirement retrieval through MCP
# /api/mcp/agent	Demonstrate Claude-driven MCP tool invocation

# This gave our backend a way to interact with the MCP server.

# Importantly, the FastAPI application is not itself the MCP server. It acts as the host application and MCP client.