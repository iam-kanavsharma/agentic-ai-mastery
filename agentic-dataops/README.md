# agentic-ai-mastery

## Project overview

agentic-dataops is a small rule-based data-operations agent and CLI for
running repeatable data transforms and data-quality checks. It demonstrates
a lightweight orchestration pattern that reads source datasets, applies
file-based "recipes" (select, filter, derive, join, groupby), runs
data-quality rules, writes cleaned outputs, and creates simple run reports.

Key features
- Recipe-driven transforms using simple YAML rules
- Data quality checks (non-null, unique, range, allowed values)
- File-based inputs/outputs (`.csv` and `.parquet`)
- Small CLI and test-suite for demos and CI

How it works (high level)
- CLI (`python -m cli`) loads a recipe and DQ rules, then calls the
  orchestrator to run the pipeline.
- The orchestrator uses `agent.core` to `load_df`, `transform`, run
  `dq_check`, then `save_df` and write a markdown report in `reports/`.
- Derived columns are evaluated with a restricted AST-based evaluator
  to avoid arbitrary `eval` execution.

## Generative AI (recipe generation)

You can use an LLM to propose recipes from a natural language description.
This repo includes a minimal OpenAI-based example:


```bash
python scripts/generate_recipe.py "Create daily revenue by region"
```

## Generative AI (recipe generation)

- For Google Vertex / Gemini (recommended):
  - Install: `pip install google-cloud-aiplatform`
  - Set service account JSON path:
    ```bash
    export GOOGLE_APPLICATION_CREDENTIALS="/path/to/sa.json"    # bash
    $env:GOOGLE_APPLICATION_CREDENTIALS = "C:\path\to\sa.json"  # PowerShell
    ```
  - Set project/location/model (example):
    ```bash
    export GOOGLE_CLOUD_PROJECT="my-gcp-project"
    export GOOGLE_CLOUD_LOCATION="us-central1"
    export VERTEX_MODEL="gemini-1.5"   # or full model resource name
    ```
  - Generate a recipe (uses Gemini by default if creds present):
    ```bash
    python scripts/generate_recipe.py "Create daily revenue by region" --out recipes/generated.json
    ```

- (Alternative) OpenAI: install `pip install openai` and set `OPENAI_API_KEY` as before; set `LLM_BACKEND=openai` to force using OpenAI.

## Environment variables and `.env`

You can copy the provided `.env.example` to `.env` and edit values there, or
export the variables directly in your shell. The repo includes LLM-related
variables for Gemini/Vertex and OpenAI.

Quick steps:

```bash
cp .env.example .env
# edit .env and fill in your values (service account path, project, model, or API key)
```

Key variables (short reference):

- `LLM_BACKEND` - `vertex` (Gemini) or `openai`. If unset, the client auto-detects.
- Vertex / Gemini:
  - `GOOGLE_APPLICATION_CREDENTIALS` - path to service-account JSON
  - `GOOGLE_CLOUD_PROJECT` - your GCP project id
  - `GOOGLE_CLOUD_LOCATION` - region (e.g. `us-central1`)
  - `VERTEX_MODEL` - model id (e.g. `gemini-1.5`) or full model resource
- OpenAI:
  - `OPENAI_API_KEY` - your OpenAI API key
  - `OPENAI_MODEL` - (optional) default OpenAI model id

Examples (bash):

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/sa.json"
export GOOGLE_CLOUD_PROJECT="my-gcp-project"
export VERTEX_MODEL="gemini-1.5"
```

PowerShell examples:

```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\path\to\sa.json"
$env:GOOGLE_CLOUD_PROJECT = "my-gcp-project"
$env:VERTEX_MODEL = "gemini-1.5"
```

After setting env vars, run the generator normally — it will prefer Vertex/Gemini
when `GOOGLE_APPLICATION_CREDENTIALS` is present or when `LLM_BACKEND` is set
to `vertex`.
The script calls the LLM and prints a JSON recipe suitable for the
existing orchestrator. You can save the recipe with `--out` and then run
the CLI using the saved recipe.

Run and mock options

The script supports `--mock` to use a canned recipe (useful for offline
testing) and `--run` to immediately execute the generated recipe via the
orchestrator. Example (mock + run):

```bash
python scripts/generate_recipe.py "Create daily revenue by region" --mock --run \
  --sales-path data/sales.csv --regions-path data/regions.csv --out-path clean/out.csv
```



## Create project folder
`mkdir agentic-dataops && cd agentic-dataops`

## (Optional) Create virtual env
`python -m venv .venv`
## Activate the virtual environment

- Windows (Command Prompt):
  `.venv\Scripts\activate`
- Windows (PowerShell):
  `.venv\Scripts\Activate.ps1`
- Windows (Git Bash / MSYS):
  `source .venv/Scripts/activate`
- macOS / Linux (bash, zsh):
  `source .venv/bin/activate`

## Install packages
`pip install -e .`

## Create folders
`mkdir -p data clean reports`

## Quickstart

### Demo Run
```
sh scripts/demo_run.sh
```

### List datasets
```
python -m agent.cli list --base-dir data
```

### Run with file-based recipe and rules
```
python -m agent.cli run "Daily Revenue by Region" \
  --sales-path data/sales.csv \
  --regions-path data/regions.csv \
  --out-path clean/revenue_by_region.csv \
  --recipe recipes/daily_revenue_by_region.yaml \
  --dq-rules rules/dq_daily_revenue.json \
  --report-title "Daily Revenue by Region - Agent Run"
```

### Show recent runs
```
python -m agent.cli history --limit 5
```
