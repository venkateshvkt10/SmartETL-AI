def build_summary(source, cleaned, cleaning_stats, errors):
    total_cells = max(int(cleaned.shape[0] * cleaned.shape[1]), 1)
    missing_cells = int(cleaned.isna().sum().sum())
    quality_score = round(100 * (total_cells - missing_cells) / total_cells, 2)
    return {
        "input_rows": int(len(source)),
        "output_rows": int(len(cleaned)),
        "duplicates_removed": int(cleaning_stats["duplicates_removed"]),
        "numeric_nulls_filled": int(cleaning_stats["numeric_nulls_filled"]),
        "validation_issues": int(len(errors)),
        "quality_score_percent": quality_score,
        "note": "Starter quality score measures non-missing cells only; extend with business rules.",
    }
