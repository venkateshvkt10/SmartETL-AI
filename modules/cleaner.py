
import pandas as pd


def clean_dataframe(
    df,
    remove_duplicates=True,
    trim_whitespace=True,
    fill_missing=False
):
    cleaned_df = df.copy()
    report = []

    original_rows = len(cleaned_df)

    # 1. Trim whitespace
    if trim_whitespace:
        text_columns = cleaned_df.select_dtypes(
            include=["object", "string"]
        ).columns

        for column in text_columns:
            cleaned_df[column] = cleaned_df[column].apply(
                lambda x: x.strip() if isinstance(x, str) else x
            )

        report.append({
            "Operation": "Trim Whitespace",
            "Result": f"{len(text_columns)} columns processed"
        })

    # 2. Convert empty strings to missing values
    text_columns = cleaned_df.select_dtypes(
        include=["object", "string"]
    ).columns

    for column in text_columns:
        cleaned_df[column] = cleaned_df[column].replace(
            r"^\s*$", pd.NA, regex=True
        )

    # 3. Remove duplicates
    duplicates_removed = 0

    if remove_duplicates:
        before = len(cleaned_df)
        cleaned_df = cleaned_df.drop_duplicates()
        duplicates_removed = before - len(cleaned_df)

        report.append({
            "Operation": "Remove Duplicates",
            "Result": f"{duplicates_removed} rows removed"
        })

    # 4. Fill missing values
    filled_cells = 0

    if fill_missing:
        for column in cleaned_df.columns:

            missing_before = cleaned_df[column].isna().sum()

            if missing_before == 0:
                continue

            if pd.api.types.is_numeric_dtype(cleaned_df[column]):
                fill_value = cleaned_df[column].median()
            else:
                modes = cleaned_df[column].mode(dropna=True)
                fill_value = modes.iloc[0] if not modes.empty else None

            if fill_value is not None and pd.notna(fill_value):
                cleaned_df[column] = cleaned_df[column].fillna(fill_value)

            filled_cells += (
                missing_before - cleaned_df[column].isna().sum()
            )

        report.append({
            "Operation": "Fill Missing Values",
            "Result": f"{filled_cells} cells filled"
        })

    final_missing = int(cleaned_df.isna().sum().sum())

    summary = {
        "original_rows": original_rows,
        "cleaned_rows": len(cleaned_df),
        "duplicates_removed": duplicates_removed,
        "filled_cells": int(filled_cells),
        "final_missing": final_missing
    }

    return cleaned_df, pd.DataFrame(report), summary
