import json
import os

import agent.memory as mem
import pandas as pd
from agent.agent_recipe_generator import generate_recipe_from_prompt
from agent.orchestrator import run_agent


class MockLLM:
    def __init__(self, text: str):
        self.text = text

    def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.0):
        return self.text


def test_generate_and_run_end_to_end(sandbox, tmp_path):
    # prepare sample data inside sandbox
    data_dir = os.path.join(mem.SAFE_ROOT, 'data')
    os.makedirs(data_dir, exist_ok=True)
    sales_fp = os.path.join(data_dir, 'sales.csv')
    regions_fp = os.path.join(data_dir, 'regions.csv')

    pd.DataFrame({
        'order_id': [1,2],
        'date': ['2025-01-01','2025-01-02'],
        'region': ['APAC','EMEA'],
        'revenue': [100,200],
    }).to_csv(sales_fp, index=False)

    pd.DataFrame({
        'region': ['APAC','EMEA'],
        'region_name': ['Asia Pacific','Europe']
    }).to_csv(regions_fp, index=False)

    # canned recipe JSON
    sample = {
        "select": ["order_id", "date", "region", "revenue"],
        "derive": [{"name": "date_day", "expr": "pd.to_datetime(df['date']).dt.date.astype(str)"}],
        "join": {"right_df": "regions", "on": ["region"], "how": "left"},
        "groupby": {"by": ["date_day","region","region_name"], "agg": {"revenue":"sum"}}
    }

    mock_text = json.dumps(sample)
    llm = MockLLM(mock_text)
    recipe = generate_recipe_from_prompt("create daily revenue by region", llm)

    out_fp = os.path.join(mem.SAFE_ROOT, 'clean', 'out.csv')
    os.makedirs(os.path.dirname(out_fp), exist_ok=True)

    inputs = {
        'sales_path': sales_fp,
        'regions_path': regions_fp,
        'recipe': recipe,
        'out_path': out_fp,
        'dq_rules': {},
        'report_title': 'Test Run'
    }

    res = run_agent('Test Run', inputs)
    assert res.get('saved', False) is True
    assert os.path.exists(out_fp)
    assert 'report_path' in res
