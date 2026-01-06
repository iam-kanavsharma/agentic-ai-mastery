# How I Learned MCP with `agentic-dataops`

The Model Context Protocol (MCP) allows AI models to interact with external data and tools. In my codebase, I used `FastMCP`, a high-level library that makes building these servers easy.

Here is a step-by-step breakdown of how I implemented it.

## 1. The Server Entry Point (`src/mcp_server/main.py`)
This file is the specific brain of my MCP application.

```python
# src/mcp_server/main.py
from mcp.server.fastmcp import FastMCP

# I initialized the server here
mcp = FastMCP("Agentic DataOps")

# ... imports ...

# I registered capabilities
register_tools(mcp)
register_resources(mcp)
```

**Key Concept**: I used `FastMCP("Name")` to create the server instance. This instance handles the communication protocol (JSON-RPC) over stdio automatically when I run `mcp.run()`.

## 2. Resources (`src/mcp_server/resources.py`)
**Resources** are how I expose *data* to the LLM. I think of them like file getters.

```python
# src/mcp_server/resources.py
@mcp.resource("file://data/{filename}")
def get_data_file(filename: str) -> str:
    """Read a CSV file from the data directory"""
    # ... implementation ...
    return file_path.read_text()
```

- **Decorator**: I used `@mcp.resource` to tell the LLM "I have data available at this pattern".
- **Function**: When the LLM asks for `file://data/sales.csv`, my function runs and returns the content string.
- **Use Case**: I use this to provide context, documentation, or raw data files (like my CSVs) to the LLM.

## 3. Tools (`src/mcp_server/tools.py`)
**Tools** are how I gave the LLM *capabilities* to do things.

```python
# src/mcp_server/tools.py
@mcp.tool()
def generate_data_recipe(prompt: str, ...) -> str:
    """
    Generates and runs a data transformation recipe...
    """
    # ... logic ...
```

- **Decorator**: I used `@mcp.tool()` to expose the Python function as a tool.
- **Type Hints**: I found these critical! MCP uses my Python type hints (`str`, `int`, etc.) to automatically generate the separate definition that tells the LLM how to use the tool.
- **Use Case**: I use this for executing code, searching databases, or in this case, generating and running a DataOps recipe.

# Practical Exercise: How I Added a Tool

I decided to add a new capability to the server: `get_system_time`.

## 1. Code Change
I modified `src/mcp_server/tools.py` to include:

```python
import datetime

@mcp.tool()
def get_system_time() -> str:
    """Returns the current system time"""
    return datetime.datetime.now().isoformat()
```

## 2. Testing It
I ran my verification script and confirmed the tool was registered:
`Registered Tools: ['generate_data_recipe', 'get_system_time']`

# Using the Server

To truly understand how a client (like Claude) sees my server, I created a demo client script.

## 1. Running the Demo Client
I run this specific command in my terminal:

```bash
python scripts/demo_client.py
```

This script:
1.  **Lists available tools**: It asks my server "What can you do?"
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
1.  I open my Claude Desktop config (usually `%APPDATA%\Claude\claude_desktop_config.json` on Windows).
2.  I add this server:

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
          "PYTHONPATH": "/ABSOLUTE/PATH/TO/agentic-dataops/src"
      }
    }
  }
}
```

# The "Why": MCP vs Internal LLM

One might ask: *"I already use Google LLM inside `generate_data_recipe`. Why do I need MCP?"*

I think of it as **Manager vs. Specialist**.

-   **The Manager (MCP Client)**: This is Claude. It has the big picture, handles the user conversation, and knows *when* to delegate.
-   **The Specialist (MCP Server)**: This is my `agentic-dataops` code. It has specific skills (DataOps), access to specific local files (CSVs), and uses its own specialized tools (Google LLM for recipe gen).

**The Workflow I Implemented**:
1.  **User**: "Claude, look at the sales data and tell me the trends."
2.  **Claude (Manager)**: "I don't have that data. But I see a tool `generate_data_recipe`. I'll ask it." -> **Calls MCP Tool**.
3.  **MCP Server (Specialist)**: Receives the request. Uses its **internal Google LLM** to write Python code to analyze the CSVs. Runs the code. Returns the *result*.
4.  **Claude (Manager)**: "Great." -> Tells user: "The data shows revenue is up..."

MCP Bridges the gap between the **General Intelligence** (Claude) and my **Specialized Logic** (DataOps + Google LLM).

# Advanced Usage: Full Workflow Demo

I updated `scripts/demo_client.py` to demonstrate the full architectural workflow:

1.  **Preparation**: I specify paths to `data/sales.csv` and `data/regions.csv`.
2.  **The Request**: My client calls `generate_data_recipe` with the prompt: *"Calculate total revenue by region"*.
3.  **The Specialist Acting**: 
    -   My server receives the filepath and prompt.
    -   It uses the **Google LLM** to internalize the schema and generate a recipe.
    -   It executes the recipe using pandas.
4.  **The Result**: My server returns the path to the report and the output CSV.

I run it myself with:
```bash
python scripts/demo_client.py
```
This lets me see the "Specialist" in action!
