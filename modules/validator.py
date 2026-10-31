import pandas as pd

def validate_dataframe(df):
    """Starter validation rules; customize required columns and rules per dataset."""
    issues = []
    for row_index, row in df.iterrows():
        for column, value in row.items():
            if pd.isna(value):
                issues.append({
                    "row_number": int(row_index) + 2,
                    "column": str(column),
                    "value": "",
                    "error_message": "Value is missing",
                })
    return pd.DataFrame(
        issues,
        columns=["row_number", "column", "value", "error_message"],
    )
