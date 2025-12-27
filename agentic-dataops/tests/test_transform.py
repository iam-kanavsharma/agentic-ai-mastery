
import pandas as pd
from agent.core import transform


def test_transform_full():
    sales = pd.DataFrame({
        'order_id': [1,2,3,4,5],
        'date': ['2025-01-01','2025-01-01','2025-01-02','2025-01-02','2025-01-02'],
        'region': ['APAC','EMEA','APAC','AMER','APAC'],
        'revenue': [1000, 800, 1200, 700, 900],
        'product_id': ['P1','P2','P1','P3','P2']
    })
    regions = pd.DataFrame({
        'region': ['APAC','EMEA','AMER'],
        'region_name': ['Asia Pacific','Europe, Middle East & Africa','Americas']
    })
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
    out = transform(sales, recipe, {'regions': regions})
    # Expect 4 groups: 2025-01-01 APAC, 2025-01-01 EMEA, 2025-01-02 AMER, 2025-01-02 APAC
    assert out.shape[0] == 4
    assert set(out.columns) == {'date_day','region','region_name','revenue'}
    # Check one value
    row = out[(out['date_day']=='2025-01-01') & (out['region']=='APAC')].iloc[0]
    assert row['revenue'] == 1000
