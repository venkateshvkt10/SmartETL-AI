
import time

from modules.cleaner import clean_dataframe
from modules.validator import validate_dataframe


def run_etl_pipeline(
    df,
    remove_duplicates=True,
    trim_whitespace=True,
    fill_missing=False,
    required_columns=None,
    unique_columns=None,
    email_columns=None,
    phone_columns=None,
    numeric_columns=None,
    date_columns=None
):
    """
    Execute the complete ETL pipeline:
    1. Transform and clean data
    2. Validate data
    3. Separate valid and rejected records
    """

    start_time = time.perf_counter()

    # Step 1: Data Cleaning
    cleaned_df, cleaning_report, cleaning_summary = clean_dataframe(
        df,
        remove_duplicates=remove_duplicates,
        trim_whitespace=trim_whitespace,
        fill_missing=fill_missing
    )

    # Step 2: Data Validation
    valid_df, rejected_df, validation_report = validate_dataframe(
        cleaned_df,
        required_columns=required_columns,
        unique_columns=unique_columns,
        email_columns=email_columns,
        phone_columns=phone_columns,
        numeric_columns=numeric_columns,
        date_columns=date_columns
    )

    # Step 3: Calculate execution time
    execution_time = round(
        time.perf_counter() - start_time, 3
    )

    # Step 4: ETL Summary
    summary = {
        "total_input_rows": len(df),
        "cleaned_rows": len(cleaned_df),
        "valid_records": len(valid_df),
        "rejected_records": len(rejected_df),
        "duplicates_removed": cleaning_summary[
            "duplicates_removed"
        ],
        "missing_cells_filled": cleaning_summary[
            "filled_cells"
        ],
        "remaining_missing_cells": cleaning_summary[
            "final_missing"
        ],
        "execution_time_seconds": execution_time,
        "pipeline_status": "Completed"
    }

    # Step 5: Return all pipeline outputs
    return {
        "cleaned_df": cleaned_df,
        "valid_df": valid_df,
        "rejected_df": rejected_df,
        "cleaning_report": cleaning_report,
        "validation_report": validation_report,
        "cleaning_summary": cleaning_summary,
        "summary": summary
    }
