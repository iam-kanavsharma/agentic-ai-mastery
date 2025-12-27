
from typing import Any, Dict

import pandas as pd
from agent.core import profile_df


def test_profile_basic():
    df = pd.DataFrame({
        'a': [1, 2, 3, 4],
        'b': ['x', 'y', 'x', None]
    })
    prof: Dict[str, Any] = profile_df(df)

    assert prof['rows'] == 4
    assert prof['cols'] == 2
    assert 'a' in prof['columns'] and 'b' in prof['columns']
    na_b = prof['columns']['b']['nulls']
    assert na_b == 1
    # numeric stats present
    num = prof['columns']['a']
    assert {'min','max','mean','std'} <= set(num.keys())
