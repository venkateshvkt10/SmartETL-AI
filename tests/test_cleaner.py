import pandas as pd
from modules.cleaner import clean_dataframe

def test_duplicate_rows_removed():
    df = pd.DataFrame({"id": [1, 1], "name": ["A", "A"]})
    cleaned, stats = clean_dataframe(df)
    assert len(cleaned) == 1
    assert stats["duplicates_removed"] == 1
