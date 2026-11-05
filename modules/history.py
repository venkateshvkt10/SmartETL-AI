from pathlib import Path
import sqlite3
from datetime import datetime
import pandas as pd

# History is stored separately from authentication data.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_FOLDER = PROJECT_ROOT / "data"
HISTORY_DB = DATA_FOLDER / "etl_history.db"
LEGACY_HISTORY_FILE = DATA_FOLDER / "etl_history.csv"

HISTORY_COLUMNS = [
    "Execution Date",
    "File Name",
    "Total Input Rows",
    "Cleaned Rows",
    "Valid Records",
    "Rejected Records",
    "Duplicates Removed",
    "Missing Cells Filled",
    "Execution Time (Seconds)",
    "Pipeline Status",
]


def _get_connection():
    DATA_FOLDER.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(HISTORY_DB, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA busy_timeout=30000")
    return connection


def _legacy_admin_id(connection):
    auth_db = DATA_FOLDER / "auth.db"
    if not auth_db.exists():
        return None

    try:
        with sqlite3.connect(auth_db, timeout=10) as auth_connection:
            row = auth_connection.execute(
                "SELECT id FROM users WHERE role = 'admin' ORDER BY id LIMIT 1"
            ).fetchone()
        return int(row[0]) if row else None
    except sqlite3.Error:
        return None


def initialize_history_db():
    """Create per-user history storage and safely migrate pre-login history."""
    with _get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS etl_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                execution_date TEXT NOT NULL,
                file_name TEXT NOT NULL,
                total_input_rows INTEGER NOT NULL DEFAULT 0,
                cleaned_rows INTEGER NOT NULL DEFAULT 0,
                valid_records INTEGER NOT NULL DEFAULT 0,
                rejected_records INTEGER NOT NULL DEFAULT 0,
                duplicates_removed INTEGER NOT NULL DEFAULT 0,
                missing_cells_filled INTEGER NOT NULL DEFAULT 0,
                execution_time_seconds REAL NOT NULL DEFAULT 0,
                pipeline_status TEXT NOT NULL DEFAULT ''
            )
        """)
        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_etl_history_user_date
            ON etl_history(user_id, execution_date)
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS history_metadata (
                meta_key TEXT PRIMARY KEY,
                meta_value TEXT NOT NULL
            )
        """)

        migrated = connection.execute(
            "SELECT meta_value FROM history_metadata WHERE meta_key = 'legacy_csv_migrated'"
        ).fetchone()

        if migrated or not LEGACY_HISTORY_FILE.exists():
            return

        admin_id = _legacy_admin_id(connection)
        # Keep legacy pre-login history private: assign it only to the admin.
        # If no admin is available yet, leave migration pending for the next run.
        if admin_id is None:
            return

        legacy_df = pd.read_csv(LEGACY_HISTORY_FILE)
        if not legacy_df.empty:
            for _, row in legacy_df.iterrows():
                values = []
                for column in HISTORY_COLUMNS:
                    value = row.get(column, "")
                    if pd.isna(value):
                        value = ""
                    values.append(value)

                connection.execute("""
                    INSERT INTO etl_history (
                        user_id, execution_date, file_name,
                        total_input_rows, cleaned_rows, valid_records,
                        rejected_records, duplicates_removed,
                        missing_cells_filled, execution_time_seconds,
                        pipeline_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    admin_id,
                    str(values[0] or datetime.now().astimezone(
                    ).isoformat(timespec="seconds")),
                    str(values[1] or "Legacy execution"),
                    int(float(values[2] or 0)),
                    int(float(values[3] or 0)),
                    int(float(values[4] or 0)),
                    int(float(values[5] or 0)),
                    int(float(values[6] or 0)),
                    int(float(values[7] or 0)),
                    float(values[8] or 0),
                    str(values[9] or "Unknown"),
                ))

        connection.execute("""
            INSERT INTO history_metadata (meta_key, meta_value)
            VALUES ('legacy_csv_migrated', ?)
        """, (datetime.now().astimezone().isoformat(timespec="seconds"),))


def _require_user_id(user_id):
    if user_id is None:
        raise ValueError(
            "A valid authenticated user ID is required for ETL history.")
    try:
        return int(user_id)
    except (TypeError, ValueError):
        raise ValueError(
            "A valid authenticated user ID is required for ETL history.")


def save_etl_history(user_id, filename, summary):
    """Save one successful ETL execution for the authenticated user."""
    user_id = _require_user_id(user_id)
    initialize_history_db()

    execution_date = datetime.now().astimezone().isoformat(timespec="seconds")

    with _get_connection() as connection:
        connection.execute("""
            INSERT INTO etl_history (
                user_id, execution_date, file_name,
                total_input_rows, cleaned_rows, valid_records,
                rejected_records, duplicates_removed,
                missing_cells_filled, execution_time_seconds,
                pipeline_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            execution_date,
            str(filename),
            int(summary["total_input_rows"]),
            int(summary["cleaned_rows"]),
            int(summary["valid_records"]),
            int(summary["rejected_records"]),
            int(summary["duplicates_removed"]),
            int(summary["missing_cells_filled"]),
            float(summary["execution_time_seconds"]),
            str(summary["pipeline_status"]),
        ))


def load_etl_history(user_id):
    """Return only the authenticated user's ETL execution history."""
    user_id = _require_user_id(user_id)
    initialize_history_db()

    with _get_connection() as connection:
        rows = connection.execute("""
            SELECT
                execution_date AS "Execution Date",
                file_name AS "File Name",
                total_input_rows AS "Total Input Rows",
                cleaned_rows AS "Cleaned Rows",
                valid_records AS "Valid Records",
                rejected_records AS "Rejected Records",
                duplicates_removed AS "Duplicates Removed",
                missing_cells_filled AS "Missing Cells Filled",
                execution_time_seconds AS "Execution Time (Seconds)",
                pipeline_status AS "Pipeline Status"
            FROM etl_history
            WHERE user_id = ?
            ORDER BY id DESC
        """, (user_id,)).fetchall()

    return pd.DataFrame([dict(row) for row in rows], columns=HISTORY_COLUMNS)


def get_etl_history_summary(user_id):
    """Calculate execution statistics for the authenticated user only."""
    history_df = load_etl_history(user_id)

    if history_df.empty:
        return {
            "total_runs": 0,
            "total_records": 0,
            "total_valid": 0,
            "total_rejected": 0,
            "average_execution_time": 0,
        }

    return {
        "total_runs": len(history_df),
        "total_records": int(history_df["Total Input Rows"].sum()),
        "total_valid": int(history_df["Valid Records"].sum()),
        "total_rejected": int(history_df["Rejected Records"].sum()),
        "average_execution_time": round(
            history_df["Execution Time (Seconds)"].mean(), 3
        ),
    }
