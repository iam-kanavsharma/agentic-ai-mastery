import sys
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.join(os.getcwd(), "src"))
from mcp.server.fastmcp import FastMCP

# Mocking FastMCP context just to load the tool function directly or we can import the module?
# The tool functions are decorated, but the underlying function is usually accessible or the module has it.
# Actually, `register_databricks_tools` defines inner functions. We can't import them easily for unit testing without mocking `mcp`.
# Alternative: Modify databricks_tools.py to expose the inner function OR use `mcp` object if we can get it.

# Let's import the register function and mess with a mock MCP object to capture the tool.
from mcp_server.databricks_tools import register_databricks_tools

class MockMCP:
    def __init__(self):
        self.tools = {}
    def tool(self, name=None):
        def decorator(func):
            self.tools[func.__name__] = func
            return func
        return decorator

def verify_databricks_mock():
    print("=== Databricks Tool Mock Verification ===")
    
    mock_mcp = MockMCP()
    register_databricks_tools(mock_mcp)
    
    tool_func = mock_mcp.tools["generate_databricks_job"]
    
    print("\n1. Running Tool with prompt: 'Calculate total revenue by region'...")
    # This triggers: Generator(PySpark) -> Reviewer -> Translator -> _submit(MOCK)
    result = tool_func(
        prompt="Calculate total revenue by region",
        sales_path="dbfs:/sales.csv", 
        regions_path="dbfs:/regions.csv"
    )
    
    print(f"\nResult:\n{result}")
    
    if "MOCK MODE" in result and "pyspark.sql" in result:
        print("\n[PASS] Successfully generated and submitted (mock) PySpark job.")
    else:
        print("\n[FAIL] Unexpected output.")

if __name__ == "__main__":
    verify_databricks_mock()
