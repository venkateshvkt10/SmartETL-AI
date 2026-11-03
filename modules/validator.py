
import re
import pandas as pd


def validate_dataframe(
    df,
    required_columns=None,
    unique_columns=None,
    email_columns=None,
    phone_columns=None,
    numeric_columns=None,
    date_columns=None
):
    required_columns = required_columns or []
    unique_columns = unique_columns or []
    email_columns = email_columns or []
    phone_columns = phone_columns or []
    numeric_columns = numeric_columns or []
    date_columns = date_columns or []

    errors = [[] for _ in range(len(df))]

    def is_missing(value):
        if pd.isna(value):
            return True
        return isinstance(value, str) and value.strip() == ""

    # 1. Required column validation
    for column in required_columns:
        for position, value in enumerate(df[column].tolist()):
            if is_missing(value):
                errors[position].append(
                    f"{column}: Required value is missing"
                )

    # 2. Duplicate key validation
    if unique_columns:
        key_data = df[unique_columns]

        # Only check rows where all key columns have values
        complete_keys = key_data.notna().all(axis=1)
        duplicate_mask = (
            complete_keys
            & key_data.duplicated(keep=False)
        )

        for position, is_duplicate in enumerate(duplicate_mask.tolist()):
            if is_duplicate:
                errors[position].append(
                    f"Duplicate key: {', '.join(unique_columns)}"
                )

    # 3. Email validation
    email_pattern = re.compile(
        r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
        r"[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$"
    )

    for column in email_columns:
        for position, value in enumerate(df[column].tolist()):
            if is_missing(value):
                continue

            if not email_pattern.fullmatch(str(value).strip()):
                errors[position].append(
                    f"{column}: Invalid email format"
                )

    # 4. Phone validation
    for column in phone_columns:
        for position, value in enumerate(df[column].tolist()):
            if is_missing(value):
                continue

            digits = re.sub(r"\D", "", str(value))

            if not 10 <= len(digits) <= 15:
                errors[position].append(
                    f"{column}: Phone number must contain 10 to 15 digits"
                )

    # 5. Numeric validation
    for column in numeric_columns:
        converted = pd.to_numeric(df[column], errors="coerce")

        for position, value in enumerate(df[column].tolist()):
            if not is_missing(value) and pd.isna(converted.iloc[position]):
                errors[position].append(
                    f"{column}: Invalid numeric value"
                )

    # 6. Date validation
    for column in date_columns:
        converted = pd.to_datetime(
            df[column],
            errors="coerce"
        )

        for position, value in enumerate(df[column].tolist()):
            if not is_missing(value) and pd.isna(converted.iloc[position]):
                errors[position].append(
                    f"{column}: Invalid date value"
                )

    # 7. Separate valid and rejected records
    has_errors = [bool(row_errors) for row_errors in errors]

    valid_df = df.iloc[
        [i for i, invalid in enumerate(has_errors) if not invalid]
    ].copy()

    rejected_df = df.iloc[
        [i for i, invalid in enumerate(has_errors) if invalid]
    ].copy()

    rejected_df["Validation Errors"] = [
        "; ".join(errors[i])
        for i, invalid in enumerate(has_errors)
        if invalid
    ]

    # Add source row numbers (header is row 1)
    rejected_df.insert(
        0,
        "Source Row",
        [i + 2 for i, invalid in enumerate(has_errors) if invalid]
    )

    total_rows = len(df)
    rejected_count = len(rejected_df)
    valid_count = len(valid_df)

    report = pd.DataFrame([
        {"Metric": "Total Records", "Count": total_rows},
        {"Metric": "Valid Records", "Count": valid_count},
        {"Metric": "Rejected Records", "Count": rejected_count},
        {
            "Metric": "Validation Success %",
            "Count": round(valid_count / total_rows * 100, 2)
            if total_rows else 0
        }
    ])

    return valid_df, rejected_df, report
