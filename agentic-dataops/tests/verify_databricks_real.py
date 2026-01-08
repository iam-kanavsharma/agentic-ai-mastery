import os
import sys
from dotenv import load_dotenv
from databricks.sdk import WorkspaceClient

# Load env vars
load_dotenv()

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

# Import the tool logic directly (bypassing MCP server for script simplicity, 
# or we could construct the tool as before). 
# We need to access the inner function of 'generate_databricks_job'.
# Since it's decorated, we can access it via the 'mock' trick or refactor.
# Let's use the mock trick which worked well in verify_databricks_mock.py.
from mcp_server.databricks_tools import register_databricks_tools

class MockMCP:
    def __init__(self):
        self.tools = {}
    def tool(self, name=None):
        def decorator(func):
            self.tools[func.__name__] = func
            return func
        return decorator

def upload_test_data(w: WorkspaceClient):
    """Uploads local data/sales.csv to DBFS"""
    local_sales = "data/sales.csv"
    local_regions = "data/regions.csv"
    
    dbfs_dir = "/FileStore/Agent_Data"
    
    print(f"Uploading data to {dbfs_dir}...")
    # Ensure local exists
    if not os.path.exists(local_sales):
        print(f"ERROR: Local file {local_sales} not found.")
        return None, None

    # Databricks SDK for DBFS/Files
    # SDK might use w.dbfs or w.files depending on version/unity catalog.
    # We will use w.files (Files API) or w.dbfs.
    # Let's try simple DBFS put.
    
    def upload(local_path, filename):
        remote_path = f"{dbfs_dir}/{filename}"
        with open(local_path, "rb") as f:
            w.dbfs.put(remote_path, f.read(), overwrite=True)
        return f"dbfs:{remote_path}"

    sales_dbfs = upload(local_sales, "sales.csv")
    regions_dbfs = upload(local_regions, "regions.csv")
    return sales_dbfs, regions_dbfs

def verify_real():
    host = os.environ.get("DATABRICKS_HOST")
    token = os.environ.get("DATABRICKS_TOKEN")
    
    if not host or not token:
        print("SKIPPING: DATABRICKS_HOST or DATABRICKS_TOKEN not set.")
        print("Please set these in .env to run real verification.")
        return

    print(f"Connecting to Databricks at {host}...")
    w = WorkspaceClient(host=host, token=token)
    
    # 1. Upload Data
    sales_path, regions_path = upload_test_data(w)
    if not sales_path:
        return

    print(f"Data uploaded to: {sales_path}, {regions_path}")

    # 2. Run Tool
    mock_mcp = MockMCP()
    register_databricks_tools(mock_mcp)
    tool_func = mock_mcp.tools["generate_databricks_job"]
    
    print("\nGenerating and Submitting Job...")
    result = tool_func(
        prompt="Calculate total revenue by region",
        sales_path=sales_path,
        regions_path=regions_path,
        out_path="/FileStore/Agent_Data/output_real.csv"
    )
    
    print(f"\nFinal Result:\n{result}")

if __name__ == "__main__":
    verify_real()
