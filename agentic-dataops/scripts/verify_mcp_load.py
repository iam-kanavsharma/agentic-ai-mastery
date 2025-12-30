import sys
import os

# Add src to path to allow direct import if installed in editable mode doesn't pick up immediately
sys.path.append(os.path.join(os.getcwd(), "src"))

try:
    from mcp_server.main import mcp
    print("SUCCESS: MCP Server imported.")
    # FastMCP stores tools in internal dicts, we can check them
    # Note: Accessing private/internal attributes for verification if public API unavailable
    tool_names = [t.name for t in mcp._tools.values()] if hasattr(mcp, "_tools") else "Unknown"
    print(f"Registered Tools: {tool_names}")
    
    # Check resources
    resource_patterns = [r.uri_template for r in mcp._resources.values()] if hasattr(mcp, "_resources") else "Unknown"
    print(f"Registered Resources: {resource_patterns}")

except ImportError as e:
    print(f"FAILURE: Could not import mcp_server.main. Error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"FAILURE: Error during inspection. Error: {e}")
    sys.exit(1)
