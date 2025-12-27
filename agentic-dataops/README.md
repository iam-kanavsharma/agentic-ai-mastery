# agentic-ai-mastery

## Create project folder
`mkdir agentic-dataops && cd agentic-dataops`

## (Optional) Create virtual env
`python -m venv .venv`
## Windows: .venv\Scripts\activate
## macOS/Linux:
`source .venv/Scripts/activate`

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
