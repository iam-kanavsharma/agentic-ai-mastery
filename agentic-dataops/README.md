# agentic-ai-mastery

## Project overview

I created **agentic-dataops** as a small rule-based data-operations agent and CLI for running repeatable data transforms and data-quality checks. The goal is to demonstrate a lightweight orchestration pattern that reads source datasets, applies file-based "recipes" (select, filter, derive, join, groupby), runs data-quality rules, writes cleaned outputs, and creates simple run reports.

### Key Features
- Recipe-driven transforms using simple YAML rules
- Data quality checks (non-null, unique, range, allowed values)
- File-based inputs/outputs (`.csv` and `.parquet`)
- Small CLI and test-suite for demos and CI

### Design Philosophy
- The CLI (`python -m cli`) loads a recipe and DQ rules, then calls the orchestrator to run the pipeline.
- The orchestrator uses `agent.core` to `load_df`, `transform`, run `dq_check`, then `save_df` and write a markdown report in `reports/`.
- I implemented a restricted AST-based evaluator for derived columns to avoid arbitrary `eval` execution.

## Generative AI (recipe generation)

The project features an LLM integration to propose recipes from a natural language description.
A minimal OpenAI-based example is included:

```bash
python scripts/generate_recipe.py "Create daily revenue by region"
```

### Supported Backends

- **Google Vertex / Gemini (Recommended)**:
  I recommend using Gemini. To set it up:
  - Install: `pip install google-cloud-aiplatform`
  - Set service account JSON path:
    ```bash
    export GOOGLE_APPLICATION_CREDENTIALS="/path/to/sa.json"
    ```
  - Set project/location/model variables.
  - Run the generator script:
    ```bash
    python scripts/generate_recipe.py "Create daily revenue by region" --out recipes/generated.json
    ```

- **OpenAI (Alternative)**: Support for OpenAI is also available if you set `LLM_BACKEND=openai` and provide `OPENAI_API_KEY`.

## Environment variables and `.env`

A `.env.example` file is provided that you can copy to `.env`. Standard environment variables are used for configuration:

```bash
cp .env.example .env
# I recommend editing .env to fill in your values
```

Key variables:
- `LLM_BACKEND`: `vertex` or `openai`.
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to safe-account key.

## Setup Instructions

1. **Create project folder**: `mkdir agentic-dataops && cd agentic-dataops`
2. **Create virtual env**: `python -m venv .venv`
3. **Activate virtual env**:
- Windows (Command Prompt):
  `.venv\Scripts\activate`
- Windows (PowerShell):
  `.venv\Scripts\Activate.ps1`
- Windows (Git Bash / MSYS):
  `source .venv/Scripts/activate`
- macOS / Linux (bash, zsh):
  `source .venv/bin/activate`
4. **Install my package**: `pip install -e .`
5. **Create data folders**: `mkdir -p data clean reports`

## Quickstart

### Demo Run
A shell script is included to run a full demo:
```
sh scripts/demo_run.sh
```

### List datasets
Use the CLI command to list available data:
```
python -m agent.cli list --base-dir data
```

### Run with file-based recipe and rules
You can run the full pipeline using the CLI:
```
python -m agent.cli run "Daily Revenue by Region" \
  --sales-path data/sales.csv \
  --regions-path data/regions.csv \
  --out-path clean/revenue_by_region.csv \
  --recipe recipes/daily_revenue_by_region.yaml \
  --dq-rules rules/dq_daily_revenue.json \
  --report-title "Daily Revenue by Region - Agent Run"
```

## MCP Server

The project also implements a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server to expose the agent's capabilities to LLM clients (like Claude Desktop).

### Features
- **Tools**: `generate_data_recipe` - Allows the LLM to generate and execute data transformations.
- **Resources**: `file://data/*.csv` - Provides direct read access to the data directory.

### Running the Server

1. **Install dependencies**: `pip install -e .`
2. **Run portions**:
   ```bash
   agentic-mcp
   ```

### Connecting to Claude Desktop
You can add the server to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "agentic-dataops": {
      "command": "python",
      "args": ["-m", "mcp_server.main"],
      "env": { "PYTHONPATH": "..." }
    }
  }
}
```
