# Learning MCP with `agentic-dataops`

The Model Context Protocol (MCP) allows AI models to interact with external data and tools. Your current codebase uses `FastMCP`, a high-level library that makes building these servers easy.

Here is a step-by-step breakdown of how it works in your project.

## 1. The Server Entry Point (`src/mcp_server/main.py`)
This file is the specific brain of your MCP application.

```python
# src/mcp_server/main.py
from mcp.server.fastmcp import FastMCP

# Initialize the server
mcp = FastMCP("Agentic DataOps")

# ... imports ...

# Register capabilities
register_tools(mcp)
register_resources(mcp)
```

**Key Concept**: `FastMCP("Name")` creates an MCP server instance. This instance will handle the communication protocol (JSON-RPC) over stdio (standard input/output) automatically when you run `mcp.run()`.

## 2. Resources (`src/mcp_server/resources.py`)
**Resources** are how you expose *data* to the LLM. Think of them like file getters.

```python
# src/mcp_server/resources.py
@mcp.resource("file://data/{filename}")
def get_data_file(filename: str) -> str:
    """Read a CSV file from the data directory"""
    # ... implementation ...
    return file_path.read_text()
```

- **Decorator**: `@mcp.resource("URI_TEMPLATE")` tells the LLM "I have data available at this pattern".
- **Function**: When the LLM asks for `file://data/sales.csv`, this function runs and returns the content string.
- **Use Case**: Providing context, documentation, or raw data files (like your CSVs) to the LLM.

## 3. Tools (`src/mcp_server/tools.py`)
**Tools** are how you give the LLM *capabilities* to do things.

```python
# src/mcp_server/tools.py
@mcp.tool()
def generate_data_recipe(prompt: str, ...) -> str:
    """
    Generates and runs a data transformation recipe...
    """
    # ... logic ...
```

- **Decorator**: `@mcp.tool()` exposes the Python function as a tool.
- **Type Hints**: Critical! MCP uses Python type hints (`str`, `int`, etc.) and docstrings to automatically generate the separate definition that tells the LLM how to use the tool.
- **Use Case**: Executing code, searching databases, or in this case, generating and running a DataOps recipe.

# Practical Exercise: Adding a Tool

We added a new capability to the server: `get_system_time`.

## 1. Code Change
We modified `src/mcp_server/tools.py` to include:

```python
import datetime

@mcp.tool()
def get_system_time() -> str:
    """Returns the current system time"""
    return datetime.datetime.now().isoformat()
```

## 2. Test It
Running our verification script confirmed the tool is registered:
`Registered Tools: ['generate_data_recipe', 'get_system_time']`

# Using the Server

To truly understand how a client (like Claude) sees your server, we created a demo client script.

## 1. Running the Demo Client
Run the following specific command in your terminal:

```bash
python scripts/demo_client.py
```

This script:
1.  **Lists available tools**: It asks the server "What can you do?"
2.  **Calls a tool**: It asks the server to execute `get_system_time`.

**Expected Output:**
```text
=== MCP Client Demo ===
1. Listing Tools...
 - get_system_time: Returns the current system time
 ...
 
2. Calling 'get_system_time'...
Result: ([TextContent(type='text', text='2026-01-05T21:10...', ...)], ...)
```

## 2. Integrating with Claude Desktop
To use this with Claude Desktop app:
1.  Open your Claude Desktop config (usually `%APPDATA%\Claude\claude_desktop_config.json` on Windows).
2.  Add this server:

```json
{
  "mcpServers": {
    "agentic-dataops": {
      "command": "python",
      "args": [
        "-m",
        "mcp_server.main"
      ],
      "env": {
          "PYTHONPATH": "C:/Users/.../agentic-dataops/src"
      }
    }
  }
}
```
*Note: You need to use the absolute path to your `src` directory in PYTHONPATH.*
