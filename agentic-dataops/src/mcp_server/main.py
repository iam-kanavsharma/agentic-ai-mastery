from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import os

# Load env vars
load_dotenv()

# Initialize FastMCP Server
mcp = FastMCP("Agentic DataOps")

# Import and register components
from .tools import register_tools
from .resources import register_resources

register_tools(mcp)
register_resources(mcp)

def main():
    mcp.run()

if __name__ == "__main__":
    main()
