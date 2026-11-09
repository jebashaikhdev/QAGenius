import sys
import json
from pathlib import Path

# Add backend directory to Python module search path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from mcp.server import MCPServer
from app.jira_service import create_jira_issue

# We initialize an MCP server and give it a name "mcp".
# This server acts as the provider of tools that our AI application can discover and invoke.

mcp = MCPServer("QAGenius MCP Server") 

# The @mcp.tool() decorator registers the Python function as an MCP tool.
# The MCP SDK uses the function's name, description and parameters to expose its tool definition.

# For example, get_requirements exposes a parameter called requirement, which is a string.
# The MCP SDK makes the tool discoverable through the MCP protocol.

@mcp.tool() 
def get_requirements(requirement: str) -> str:
    """ Retrieve the software requirements provided to QAGenius."""
    return requirement

@mcp.tool()
def save_test_cases(test_cases: str) -> str:
    """ Save approved test cases. This demo tool currently returns a confirmation."""
    return f"Test cases recieved for saving:\n {test_cases}"

@mcp.tool()
async def create_jira_issue_tool(
    summary: str,
    description: str
) -> str:
    """Create a jira task for an approved QA test case."""
    
    result = await create_jira_issue(
        summary=summary,
        description=description
    )
    
    return json.dumps({
        "key": result["key"],
        "id": result["id"]
        })
    


# This starts the MCP server when the Python file is executed directly.
# We use this server as a separate process launched by our MCP client.
if __name__ == "__main__":
    mcp.run()
    