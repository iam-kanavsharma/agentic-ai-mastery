import sys
import os
import signal
import time

# Add src to path to allow direct import if installed in editable mode doesn't pick up immediately
sys.path.append(os.path.join(os.getcwd(), "src"))

def timeout_handler(signum, frame):
    raise TimeoutError("Import timed out")

# Set 10s timeout
signal.signal(signal.SIGALRM, timeout_handler) if hasattr(signal, "SIGALRM") else None
# Windows doesn't support SIGALRM easily, so we might skip signal on Windows or use a different approach.
# Since user is on Windows, let's just use simple prints before/after.

try:
    print("Attempting to import mcp_server.main...")
    start_time = time.time()
    from mcp_server.main import mcp
    print(f"SUCCESS: MCP Server imported in {time.time() - start_time:.2f}s.")
    
    # FastMCP stores tools in internal dicts, we can check them
    # Updated to check _tool_manager for newer FastMCP versions
    if hasattr(mcp, "_tool_manager") and hasattr(mcp._tool_manager, "_tools"):
         tool_names = list(mcp._tool_manager._tools.keys())
    elif hasattr(mcp, "_tools"):
         tool_names = [t.name for t in mcp._tools.values()]
    else:
         tool_names = "Unknown"
    
    print(f"Registered Tools: {tool_names}")
    
    # Check resources
    resource_patterns = [r.uri_template for r in mcp._resources.values()] if hasattr(mcp, "_resources") else "Unknown"
    print(f"Registered Resources: {resource_patterns}")

except ImportError as e:
    print(f"FAILURE: Could not import mcp_server.main. Error: {e}")
    print("Hint: Ensure 'mcp_server' is listed in pyproject.toml packages.")
    sys.exit(1)
except Exception as e:
    print(f"FAILURE: Error during inspection. Error: {e}")
    sys.exit(1)
