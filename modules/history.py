
from pathlib import Path
from datetime import datetime

import pandas as pd


# Store execution history in the project data folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_FOLDER = PROJECT_ROOT / "data"
HISTORY_FILE = DATA_FOLDER / "etl_history.csv"


def save_etl_history(filename, summary):
    """
    Save metadata for one successful ETL execution.
    Uploaded dataset contents are not stored.
    """

    DATA_FOLDER.mkdir(parents=True, exist_ok=True)

    history_record = {
        "Execution Date": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "File Name": filename,
        "Total Input Rows": summary["total_input_rows"],
        "Cleaned Rows": summary["cleaned_rows"],
        "Valid Records": summary["valid_records"],
        "Rejected Records": summary["rejected_records"],
        "Duplicates Removed": summary["duplicates_removed"],
        "Missing Cells Filled": summary["missing_cells_filled"],
        "Execution Time (Seconds)": summary["execution_time_seconds"],
        "Pipeline Status": summary["pipeline_status"]
    }

    history_df = pd.DataFrame([history_record])

    if HISTORY_FILE.exists():
        history_df.to_csv(
            HISTORY_FILE,
            mode="a",
            header=False,
            index=False
        )
    else:
        history_df.to_csv(
            HISTORY_FILE,
            index=False
        )


def load_etl_history():
    """
    Read previously saved ETL execution history.
    """

    if not HISTORY_FILE.exists():
        return pd.DataFrame()

    return pd.read_csv(HISTORY_FILE)


def get_etl_history_summary():
    """
    Calculate overall execution statistics.
    """

    history_df = load_etl_history()

    if history_df.empty:
        return {
            "total_runs": 0,
            "total_records": 0,
            "total_valid": 0,
            "total_rejected": 0,
            "average_execution_time": 0
        }

    return {
        "total_runs": len(history_df),
        "total_records": int(
            history_df["Total Input Rows"].sum()
        ),
        "total_valid": int(
            history_df["Valid Records"].sum()
        ),
        "total_rejected": int(
            history_df["Rejected Records"].sum()
        ),
        "average_execution_time": round(
            history_df["Execution Time (Seconds)"].mean(),
            3
        )
    }
