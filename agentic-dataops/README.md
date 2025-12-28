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
python -m cli list --base-dir data
```

### Run with file-based recipe and rules
```
python -m cli run "Daily Revenue by Region" \
  --sales-path data/sales.csv \
  --regions-path data/regions.csv \
  --out-path clean/revenue_by_region.csv \
  --recipe recipes/daily_revenue_by_region.yaml \
  --dq-rules rules/dq_daily_revenue.json \
  --report-title "Daily Revenue by Region - Agent Run"
```

### Show recent runs
```
python -m cli history --limit 5
```
