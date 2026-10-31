import streamlit as st
import pandas as pd
from modules.file_reader import read_uploaded_file
from modules.cleaner import clean_dataframe
from modules.validator import validate_dataframe
from modules.report import build_summary

st.set_page_config(page_title="SmartETL AI", page_icon="🧹", layout="wide")
st.title("🧹 SmartETL AI")
st.caption("Upload • Profile • Clean • Validate • Export")

with st.sidebar:
    st.header("Cleaning options")
    remove_duplicates = st.checkbox("Remove exact duplicate rows", value=True)
    null_strategy = st.selectbox(
        "Fill numeric null values with",
        ["Do not fill", "Mean", "Median", "Zero"],
    )
    trim_text = st.checkbox("Trim leading/trailing spaces", value=True)

uploaded = st.file_uploader("Upload a CSV, Excel or JSON file", type=["csv", "xlsx", "xls", "json"])

if uploaded:
    try:
        df = read_uploaded_file(uploaded)
        st.subheader("Source preview")
        st.write(f"Rows: **{len(df):,}** · Columns: **{len(df.columns)}**")
        st.dataframe(df.head(100), use_container_width=True)

        if st.button("Run ETL", type="primary"):
            cleaned, cleaning_stats = clean_dataframe(
                df,
                remove_duplicates=remove_duplicates,
                null_strategy=null_strategy,
                trim_text=trim_text,
            )
            errors = validate_dataframe(cleaned)
            summary = build_summary(df, cleaned, cleaning_stats, errors)

            st.session_state["cleaned"] = cleaned
            st.session_state["errors"] = errors
            st.session_state["summary"] = summary
            st.success("ETL run completed.")

    except Exception as exc:
        st.error(f"Unable to read this file: {exc}")

if "cleaned" in st.session_state:
    cleaned = st.session_state["cleaned"]
    errors = st.session_state["errors"]
    summary = st.session_state["summary"]

    st.subheader("ETL results")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Input rows", summary["input_rows"])
    c2.metric("Output rows", summary["output_rows"])
    c3.metric("Duplicates removed", summary["duplicates_removed"])
    c4.metric("Validation issues", len(errors))

    st.subheader("Cleaned data preview")
    st.dataframe(cleaned.head(100), use_container_width=True)

    st.subheader("Validation issues")
    if errors.empty:
        st.success("No validation issues found by the starter rules.")
    else:
        st.dataframe(errors, use_container_width=True)
        st.download_button(
            "Download validation report (CSV)",
            errors.to_csv(index=False).encode("utf-8"),
            file_name="validation_report.csv",
            mime="text/csv",
        )

    st.download_button(
        "Download cleaned data (CSV)",
        cleaned.to_csv(index=False).encode("utf-8"),
        file_name="cleaned_data.csv",
        mime="text/csv",
    )
    st.download_button(
        "Download cleaned data (Excel)",
        data=__import__("modules.exporter", fromlist=["to_excel_bytes"]).to_excel_bytes(cleaned),
        file_name="cleaned_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.subheader("Execution summary")
    st.json(summary)
