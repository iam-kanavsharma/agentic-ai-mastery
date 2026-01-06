# Learning MCP with `agentic-dataops`

The Model Context Protocol (MCP) allows AI models to interact with external data and tools. Your current codebase uses `FastMCP`, a high-level library that makes building these servers easy.

Here is a step-by-step breakdown of how it works in your project.

## 1. The Server Entry Point (`src/mcp_server/main.py`)
This file is the specific brain of your MCP APPLICATION.

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

# The "Why": MCP vs Internal LLM

You might ask: *"We already use Google LLM inside `generate_data_recipe`. Why do we need MCP?"*

Think of it as **Manager vs. Specialist**.

-   **The Manager (MCP Client)**: This is Claude (or any other intelligent interface). It has the big picture, handles the user conversation, and knows *when* to delegate.
-   **The Specialist (MCP Server)**: This is your `agentic-dataops`. It has specific skills (DataOps), access to specific local files (CSVs), and uses its own specialized tools (Google LLM for recipe gen).

**The Workflow**:
1.  **User**: "Claude, look at the sales data and tell me the trends."
2.  **Claude (Manager)**: "I don't have that data. But I see a tool `generate_data_recipe`. I'll ask it." -> **Calls MCP Tool**.
3.  **MCP Server (Specialist)**: Receives the request. Uses its **internal Google LLM** to write Python code to analyze the CSVs. Runs the code. Returns the *result* (e.g., "Revenue up 20%").
4.  **Claude (Manager)**: "Great." -> Tells user: "The data shows revenue is up 20%..."

MCP Bridges the gap between the **General Intelligence** (Claude) and your **Specialized Logic** (DataOps + Google LLM).

# Advanced Usage: Full Workflow Demo

We updated `scripts/demo_client.py` to demonstrate the full architectural workflow:

1.  **Preparation**: We specify paths to `data/sales.csv` and `data/regions.csv`.
2.  **The Request**: The client calls `generate_data_recipe` with the prompt: *"Calculate total revenue by region"*.
3.  **The Specialist Acting**: 
    -   The server received the filepath and prompt.
    -   It used the **Google LLM** to internalize the schema and generate a recipe.
    -   It executed the recipe using pandas.
4.  **The Result**: The server returned the path to the report and the output CSV.

Run it yourself:
```bash
python scripts/demo_client.py
```
You will see the "Specialist" in action, generating a real DataOps report!
