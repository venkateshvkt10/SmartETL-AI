
import pandas as pd


def profile_dataframe(df):

    rows, columns = df.shape
    total_cells = rows * columns

    column_stats = []

    for column in df.columns:

        series = df[column]

        null_count = int(series.isna().sum())
        unique_count = int(series.nunique(dropna=True))

        samples = (
            series.dropna()
            .astype(str)
            .drop_duplicates()
            .head(3)
            .tolist()
        )

        column_stats.append({
            "Column": str(column),
            "Data Type": str(series.dtype),
            "Total Values": int(series.notna().sum()),
            "Null Count": null_count,
            "Null %": round(
                null_count / rows * 100, 2
            ) if rows else 0,
            "Unique Values": unique_count,
            "Repeated Values": int(
                series.notna().sum() - unique_count
            ),
            "Sample Values": ", ".join(samples)
        })

    null_cells = int(df.isna().sum().sum())

    completeness = (
        round(
            (total_cells - null_cells)
            / total_cells * 100, 2
        )
        if total_cells else 100
    )

    return {
        "row_count": rows,
        "column_count": columns,
        "duplicate_rows": int(df.duplicated().sum()),
        "null_cells": null_cells,
        "completeness": completeness,
        "columns": pd.DataFrame(column_stats)
    }
