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

    print("\n3. Calling 'generate_data_recipe' (The Specialist)...")
    try:
        # We use absolute paths to ensure the server finds them
        base_dir = os.path.dirname(os.path.abspath(__file__)) # scripts/
        project_root = os.path.dirname(base_dir)
        sales_path = os.path.join(project_root, "data", "sales.csv")
        regions_path = os.path.join(project_root, "data", "regions.csv")
        out_path = os.path.join(project_root, "revenue_analysis_output.csv")
        
        print(f" - Prompt: 'Calculate total revenue by region'")
        print(f" - Sales: {sales_path}")
        
        result = await mcp.call_tool("generate_data_recipe", arguments={
            "prompt": "Calculate total revenue by region",
            "sales_path": sales_path,
            "regions_path": regions_path,
            "out_path": out_path
        })
        print(f"Result: {result}")
        
    except Exception as e:
        print(f"Error calling recipe tool: {e}")

if __name__ == "__main__":
    asyncio.run(main())
