import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from mcp_server.main import mcp

print("MCP Object dir:", dir(mcp))
if hasattr(mcp, "_tool_manager"):
     print("_tool_manager:", dir(mcp._tool_manager))
     if hasattr(mcp._tool_manager, "_tools"):
         print("Tools in manager:", mcp._tool_manager._tools.keys())
