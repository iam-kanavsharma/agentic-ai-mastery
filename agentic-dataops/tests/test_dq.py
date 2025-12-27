
import pandas as pd
from agent.core import dq_check


def test_dq_pass():
    df = pd.DataFrame({
        'order_id': [1,2,3],
        'revenue': [100, 200, 300],
        'region': ['APAC','EMEA','AMER']
    })
    rules = {
        'non_null': ['order_id','revenue','region'],
        'unique': ['order_id'],
        'range': {'revenue': {'min': 0}},
        'allowed_values': {'region': ['APAC','EMEA','AMER']}
    }
    ok, issues = dq_check(df, rules)
    assert ok
    assert issues == []

def test_dq_fail():
    df = pd.DataFrame({
        'order_id': [1,1,2],  # duplicate
        'revenue': [100, -5, 300],  # negative
        'region': ['APAC','BAD','AMER']
    })
    rules = {
        'non_null': ['order_id','revenue','region'],
        'unique': ['order_id'],
        'range': {'revenue': {'min': 0}},
        'allowed_values': {'region': ['APAC','EMEA','AMER']}
    }
    ok, issues = dq_check(df, rules)
    assert not ok
    assert any('Unique violation' in s for s in issues)
    assert any('Range violation' in s for s in issues)
    assert any('Allowed-values violation' in s for s in issues)
