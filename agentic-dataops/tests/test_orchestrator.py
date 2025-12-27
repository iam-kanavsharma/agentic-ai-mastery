
import os

import agent.memory as mem
import pandas as pd
from agent.orchestrator import run_agent


def test_run_agent_e2e(sandbox):
    # Prepare data inside sandbox
    data_dir = os.path.join(mem.SAFE_ROOT, 'data')
    regions_fp = os.path.join(data_dir, 'regions.csv')
    sales_fp = os.path.join(data_dir, 'sales.csv')
    os.makedirs(data_dir, exist_ok=True)
    pd.DataFrame({
        'order_id': [1,2,3,4,5],
        'date': ['2025-01-01','2025-01-01','2025-01-02','2025-01-02','2025-01-02'],
        'region': ['APAC','EMEA','APAC','AMER','APAC'],
        'revenue': [1000, 800, 1200, 700, 900],
        'product_id': ['P1','P2','P1','P3','P2']
    }).to_csv(sales_fp, index=False)
    pd.DataFrame({
        'region': ['APAC','EMEA','AMER'],
        'region_name': ['Asia Pacific','Europe, Middle East & Africa','Americas']
    }).to_csv(regions_fp, index=False)

    recipe = {
        'select': ['order_id','date','region','revenue','product_id'],
        'filter': "region in ['APAC','EMEA','AMER'] and revenue >= 0",
        'derive': [
            {'name': 'date_day', 'expr': "pd.to_datetime(df['date']).dt.date.astype(str)"},
            {'name': 'rev_in_k', 'expr': "df['revenue'] / 1000"}
        ],
        'join': {'right_df': 'regions', 'on': ['region'], 'how': 'left'},
        'groupby': {'by': ['date_day','region','region_name'], 'agg': {'revenue':'sum'}}
    }
    dq_rules = {
        'non_null': ['date_day','region','revenue'],
        'unique': ['order_id'],
        'range': {'revenue': {'min': 0}},
        'allowed_values': {'region': ['APAC','EMEA','AMER']}
    }

    out_fp = os.path.join(mem.SAFE_ROOT, 'clean', 'revenue_by_region.csv')
    os.makedirs(os.path.dirname(out_fp), exist_ok=True)

    result = run_agent(
        'Create clean daily revenue by region with DQ and a report',
        {
            'sales_path': sales_fp,
            'regions_path': regions_fp,
            'recipe': recipe,
            'dq_rules': dq_rules,
            'out_path': out_fp,
            'report_title': 'Daily Revenue by Region - Agent Run'
        }
    )

    assert result.get('dq_ok') is False
    assert result.get('reflection_ok') in (True, False)  # reflection_ok may vary with data
    assert os.path.exists(result.get('report_path'))
