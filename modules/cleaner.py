import pandas as pd

def clean_dataframe(df, remove_duplicates=True, null_strategy="Do not fill", trim_text=True):
    result = df.copy()
    before = len(result)

    # Treat whitespace-only strings as missing values.
    result = result.replace(r"^\s*$", pd.NA, regex=True)

    if trim_text:
        for col in result.select_dtypes(include=["object", "string"]).columns:
            result[col] = result[col].map(
                lambda value: value.strip() if isinstance(value, str) else value
            )

    duplicates_removed = 0
    if remove_duplicates:
        result = result.drop_duplicates()
        duplicates_removed = before - len(result)

    filled_cells = 0
    if null_strategy != "Do not fill":
        for col in result.select_dtypes(include="number").columns:
            missing = int(result[col].isna().sum())
            if missing == 0:
                continue
            if null_strategy == "Mean":
                fill_value = result[col].mean()
            elif null_strategy == "Median":
                fill_value = result[col].median()
            else:
                fill_value = 0
            if pd.notna(fill_value):
                result[col] = result[col].fillna(fill_value)
                filled_cells += missing

    stats = {
        "duplicates_removed": duplicates_removed,
        "numeric_nulls_filled": filled_cells,
        "input_rows": before,
        "output_rows": len(result),
    }
    return result, stats
