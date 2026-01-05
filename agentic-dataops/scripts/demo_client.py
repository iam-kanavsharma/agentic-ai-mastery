import sys
import os
import asyncio

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from mcp_server.main import mcp

async def main():
    print("=== MCP Client Demo ===")
    print("1. Listing Tools...")
    # Accessing tools programmatically (simulating what a client does via discovery)
    tools = await mcp.list_tools()
    for t in tools:
        print(f" - {t.name}: {t.description}")
        
    print("\n2. Calling 'get_system_time'...")
    try:
        # FastMCP allows direct calling for testing
        result = await mcp.call_tool("get_system_time", arguments={})
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error calling tool: {e}")

if __name__ == "__main__":
    asyncio.run(main())
