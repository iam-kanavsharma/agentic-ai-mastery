#!/usr/bin/env bash
set -euo pipefail
set -e

export PYTHONPATH="src:${PYTHONPATH:-}"

GOAL="Generate clean daily revenue by region with DQ and report"
SALES_PATH="data/sales.csv"
REGIONS_PATH="data/regions.csv"
OUT_PATH="clean/revenue_by_region.csv"
RECIPE_PATH="recipes/daily_revenue_by_region.yaml"
DQ_RULES_PATH="rules/dq_daily_revenue.json"
REPORT_TITLE="Daily Revenue by Region - Demo Run"

mkdir -p data clean reports recipes rules

# Sample data
[ ! -f "$SALES_PATH" ] && cat > "$SALES_PATH" <<EOF
order_id,date,region,revenue,product_id
1,2025-01-01,APAC,1000,P1
2,2025-01-01,EMEA,800,P2
3,2025-01-02,APAC,1200,P1
4,2025-01-02,AMER,700,P3
5,2025-01-02,APAC,900,P2
EOF

[ ! -f "$REGIONS_PATH" ] && cat > "$REGIONS_PATH" <<EOF
region,region_name
APAC,Asia Pacific
EMEA,Europe, Middle East & Africa
AMER,Americas
EOF

# Sample recipe
[ ! -f "$RECIPE_PATH" ] && cat > "$RECIPE_PATH" <<EOF
select: ["order_id","date","region","revenue","product_id"]
filter: "region in ['APAC','EMEA','AMER'] and revenue >= 0"
derive:
  - name: date_day
    expr: "pd.to_datetime(df['date']).dt.date.astype(str)"
  - name: rev_in_k
    expr: "df['revenue'] / 1000"
join:
  right_df: "regions"
  on: ["region"]
  how: "left"
groupby:
  by: ["date_day","region","region_name"]
  agg: {"revenue": "sum"}
EOF

# Sample DQ rules
[ ! -f "$DQ_RULES_PATH" ] && cat > "$DQ_RULES_PATH" <<EOF
{
  "non_null": ["date_day","region","revenue"],
  "unique": ["order_id"],
  "range": {"revenue": {"min": 0}},
  "allowed_values": {"region": ["APAC","EMEA","AMER"]}
}
EOF

python -m agent.cli test
if [ $? -ne 0 ]; then
  echo "Tests failed"; exit 1
else
  echo "Tests passed"
fi

echo "Running DataOps agent..."
python -X dev -X tracemalloc=5 -m agent.cli run "$GOAL" \
  --sales-path "$SALES_PATH" \
  --regions-path "$REGIONS_PATH" \
  --out-path "$OUT_PATH" \
  --recipe "$RECIPE_PATH" \
  --dq-rules "$DQ_RULES_PATH" \
  --report-title "$REPORT_TITLE"

echo "Done. Output in 'clean/', report in 'reports/'."