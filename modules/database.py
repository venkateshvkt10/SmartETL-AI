
import json
import uuid

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


# SQL Server configuration
SERVER = "localhost"
DATABASE = "SmartETL_AI"
DRIVER = "ODBC Driver 18 for SQL Server"

CONNECTION_STRING = (
    f"DRIVER={{{DRIVER}}};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

connection_url = URL.create(
    "mssql+pyodbc",
    query={"odbc_connect": CONNECTION_STRING}
)

engine = create_engine(
    connection_url,
    fast_executemany=True,
    pool_pre_ping=True
)


def test_database_connection():
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT DB_NAME()")
        )
        return result.scalar()


def load_valid_records(df, source_file_name):
    if df.empty:
        raise ValueError("No valid records available to load.")

    if df.columns.duplicated().any():
        raise ValueError("Duplicate column names are not supported.")

    reserved_columns = {"ETL_Batch_ID", "ETL_Source_File"}

    if reserved_columns.intersection(df.columns):
        raise ValueError(
            "Dataset contains reserved SmartETL metadata columns."
        )

    batch_id = str(uuid.uuid4())
    total_records = len(df)

    # Prepare staging records
    staging_df = pd.DataFrame({
        "BatchID": [batch_id] * total_records,
        "SourceFileName": [source_file_name] * total_records,
        "RecordData": [
            json.dumps(record, default=str)
            for record in df.to_dict(orient="records")
        ]
    })

    # Prepare target records
    target_df = df.copy()
    target_df["ETL_Batch_ID"] = batch_id
    target_df["ETL_Source_File"] = source_file_name

    try:
        # Keep staging, target and success log in one transaction
        with engine.begin() as connection:

            staging_df.to_sql(
                name="ETL_Staging",
                con=connection,
                schema="dbo",
                if_exists="append",
                index=False
            )

            target_df.to_sql(
                name="Validated_Records",
                con=connection,
                schema="dbo",
                if_exists="append",
                index=False
            )

            connection.execute(
                text("""
                    INSERT INTO dbo.ETL_Load_History (
                        BatchID,
                        SourceFileName,
                        TotalRecords,
                        SuccessfulRecords,
                        FailedRecords,
                        LoadStatus,
                        ErrorMessage
                    )
                    VALUES (
                        :batch_id,
                        :filename,
                        :total,
                        :success,
                        :failed,
                        :status,
                        :error
                    )
                """),
                {
                    "batch_id": batch_id,
                    "filename": source_file_name,
                    "total": total_records,
                    "success": total_records,
                    "failed": 0,
                    "status": "SUCCESS",
                    "error": None
                }
            )

        return {
            "batch_id": batch_id,
            "total_records": total_records,
            "successful_records": total_records,
            "failed_records": 0,
            "status": "SUCCESS"
        }

    except Exception as error:

        # Record the failed load separately
        try:
            with engine.begin() as connection:
                connection.execute(
                    text("""
                        INSERT INTO dbo.ETL_Load_History (
                            BatchID,
                            SourceFileName,
                            TotalRecords,
                            SuccessfulRecords,
                            FailedRecords,
                            LoadStatus,
                            ErrorMessage
                        )
                        VALUES (
                            :batch_id,
                            :filename,
                            :total,
                            0,
                            :failed,
                            'FAILED',
                            :error
                        )
                    """),
                    {
                        "batch_id": batch_id,
                        "filename": source_file_name,
                        "total": total_records,
                        "failed": total_records,
                        "error": str(error)[:4000]
                    }
                )
        except Exception as log_error:
            raise RuntimeError(
                f"Database load failed: {error}. "
                f"Failure logging also failed: {log_error}"
            ) from error

        raise RuntimeError(
            f"Database load failed: {error}"
        ) from error
