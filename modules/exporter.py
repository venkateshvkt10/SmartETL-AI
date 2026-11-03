
from io import BytesIO
import pandas as pd


def dataframe_to_csv(df):
    """Convert DataFrame into downloadable CSV bytes."""

    return df.to_csv(index=False).encode("utf-8-sig")


def dataframe_to_excel(df, sheet_name="Data"):
    """Convert DataFrame into downloadable Excel bytes."""

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(
            writer,
            index=False,
            sheet_name=sheet_name
        )

    output.seek(0)
    return output.getvalue()


def create_etl_excel_report(
    cleaned_df,
    valid_df,
    rejected_df,
    cleaning_report,
    validation_report,
    summary
):
    """Create one Excel workbook containing all ETL results."""

    output = BytesIO()

    summary_df = pd.DataFrame(
        list(summary.items()),
        columns=["Metric", "Value"]
    )

    with pd.ExcelWriter(output, engine="openpyxl") as writer:

        cleaned_df.to_excel(
            writer,
            index=False,
            sheet_name="Cleaned_Data"
        )

        valid_df.to_excel(
            writer,
            index=False,
            sheet_name="Valid_Records"
        )

        rejected_df.to_excel(
            writer,
            index=False,
            sheet_name="Rejected_Records"
        )

        cleaning_report.to_excel(
            writer,
            index=False,
            sheet_name="Cleaning_Report"
        )

        validation_report.to_excel(
            writer,
            index=False,
            sheet_name="Validation_Report"
        )

        summary_df.to_excel(
            writer,
            index=False,
            sheet_name="ETL_Summary"
        )

    output.seek(0)
    return output.getvalue()
