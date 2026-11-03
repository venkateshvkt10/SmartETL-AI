
import streamlit as st
import hashlib

from modules.file_reader import read_uploaded_file
from modules.profiler import profile_dataframe
from modules.cleaner import clean_dataframe
from modules.validator import validate_dataframe
from modules.pipeline import run_etl_pipeline
from modules.exporter import (
    dataframe_to_csv,
    dataframe_to_excel,
    create_etl_excel_report
)
from modules.history import (
    save_etl_history,
    load_etl_history,
    get_etl_history_summary
)


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="SmartETL AI",
    page_icon="🧹",
    layout="wide"
)

st.title("🧹 SmartETL AI")
st.caption("Intelligent ETL and Data Quality Platform")


# --------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------

st.sidebar.title("SmartETL AI")
st.sidebar.caption("Data Engineering Platform")

selected_page = st.sidebar.radio(
    "Navigation",
    [
        "Home",
        "Data Preparation",
        "Complete ETL Pipeline",
        "ETL Dashboard"
    ]
)

st.sidebar.divider()
st.sidebar.info("Phases 1–4 completed | Phase 5 in progress")

MAX_FILE_SIZE_MB = 50


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

if selected_page == "Home":

    st.header("Welcome to SmartETL AI")

    st.write(
        "A Python-based ETL and data quality platform "
        "for profiling, cleaning, validating and processing data."
    )

    st.subheader("Project Development Progress")

    phases = [
        ("Phase 1", "Project Setup & GitHub", "Completed"),
        ("Phase 2", "File Upload & Data Profiling", "Completed"),
        ("Phase 3", "Data Cleaning", "Completed"),
        ("Phase 4", "Data Validation", "Completed"),
        ("Phase 5", "Complete ETL Pipeline & Export", "In Progress"),
        ("Phase 6", "ETL Dashboard & Execution History", "Upcoming"),
        ("Phase 7", "AI-Powered Data Quality Reports", "Upcoming"),
        ("Phase 8", "Database Integration", "Upcoming"),
        ("Phase 9", "Deployment & Security", "Upcoming")
    ]

    for phase, name, status in phases:

        col1, col2, col3 = st.columns([1, 4, 2])

        col1.write(f"**{phase}**")
        col2.write(name)

        if status == "Completed":
            col3.success("Completed")
        elif status == "In Progress":
            col3.warning("In Progress")
        else:
            col3.info("Upcoming")

    st.divider()

    st.subheader("Technology Stack")

    t1, t2, t3, t4 = st.columns(4)

    t1.metric("Language", "Python")
    t2.metric("Framework", "Streamlit")
    t3.metric("Data Processing", "Pandas")
    t4.metric("Export", "CSV / Excel")

    st.info(
        "Select Data Preparation or Complete ETL Pipeline "
        "from the sidebar to start processing your data."
    )


# --------------------------------------------------
# DATA PAGES - FILE UPLOAD
# --------------------------------------------------

elif selected_page in [
    "Data Preparation",
    "Complete ETL Pipeline"
]:

    if selected_page == "Data Preparation":
        st.header("Data Preparation")
        st.caption(
            "Phase 2: Upload and Profile | "
            "Phase 3: Cleaning | Phase 4: Validation"
        )

    else:
        st.header("Complete ETL Pipeline")
        st.caption(
            "Extract → Transform → Validate → Export"
        )

    uploaded_file = st.file_uploader(
        "Upload your dataset",
        type=["csv", "xlsx", "xls", "json"],
        key="dataset_uploader"
    )

    if uploaded_file:

        if uploaded_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
            st.error("File exceeds the 50 MB limit.")
            st.stop()

        try:

            file_hash = hashlib.sha256(
                uploaded_file.getvalue()
            ).hexdigest()

            df = read_uploaded_file(uploaded_file)

            if df.empty:
                st.warning("Uploaded file contains no records.")
                st.stop()

            if df.columns.duplicated().any():
                st.error("Duplicate column names detected.")
                st.stop()

            st.success("File uploaded successfully!")

            # ==========================================
            # PAGE 1: DATA PREPARATION
            # ==========================================

            if selected_page == "Data Preparation":

                # PHASE 2 - FILE INFORMATION

                st.subheader("1. File Information")

                col1, col2, col3 = st.columns(3)

                col1.metric("File Name", uploaded_file.name)
                col2.metric("Rows", f"{len(df):,}")
                col3.metric("Columns", len(df.columns))

                # DATA PREVIEW

                st.subheader("2. Data Preview")

                st.dataframe(
                    df.head(100),
                    use_container_width=True
                )

                # DATA PROFILING

                st.subheader("3. Data Quality Profile")

                profile = profile_dataframe(df)

                c1, c2, c3, c4 = st.columns(4)

                c1.metric(
                    "Total Records",
                    f"{profile['row_count']:,}"
                )

                c2.metric(
                    "Duplicate Rows",
                    f"{profile['duplicate_rows']:,}"
                )

                c3.metric(
                    "Missing Cells",
                    f"{profile['null_cells']:,}"
                )

                c4.metric(
                    "Completeness",
                    f"{profile['completeness']}%"
                )

                st.subheader("4. Column-Level Analysis")

                st.dataframe(
                    profile["columns"],
                    use_container_width=True
                )

                st.subheader("5. Descriptive Statistics")

                with st.expander("View statistical analysis"):

                    try:
                        st.dataframe(
                            df.describe(include="all").transpose(),
                            use_container_width=True
                        )

                    except Exception:
                        st.info(
                            "Statistical analysis is unavailable."
                        )

                st.subheader("6. Missing Value Analysis")

                null_summary = profile["columns"][
                    ["Column", "Null Count", "Null %"]
                ]

                st.dataframe(
                    null_summary,
                    use_container_width=True
                )

                st.success("Data profiling completed!")

                # PHASE 3 - DATA CLEANING

                st.divider()

                st.header("7. Data Cleaning")

                remove_duplicates = st.checkbox(
                    "Remove duplicate rows",
                    value=True,
                    key="remove_duplicates"
                )

                trim_whitespace = st.checkbox(
                    "Trim leading and trailing spaces",
                    value=True,
                    key="trim_whitespace"
                )

                fill_missing = st.checkbox(
                    "Fill missing values",
                    value=False,
                    key="fill_missing"
                )

                if fill_missing:
                    st.warning(
                        "Numeric values use median and text values "
                        "use the most frequent value."
                    )

                if st.button(
                    "Run Data Cleaning",
                    type="primary"
                ):

                    cleaned_df, cleaning_report, summary = (
                        clean_dataframe(
                            df,
                            remove_duplicates=remove_duplicates,
                            trim_whitespace=trim_whitespace,
                            fill_missing=fill_missing
                        )
                    )

                    st.session_state["cleaned_df"] = cleaned_df
                    st.session_state["cleaning_report"] = cleaning_report
                    st.session_state["cleaning_summary"] = summary
                    st.session_state["preparation_source"] = file_hash

                    for key in [
                        "valid_df",
                        "rejected_df",
                        "validation_report",
                        "validation_source"
                    ]:
                        st.session_state.pop(key, None)

                    st.success("Data cleaning completed!")

                # DISPLAY CLEANING RESULTS

                if (
                    "cleaned_df" in st.session_state
                    and st.session_state.get("preparation_source")
                    == file_hash
                ):

                    cleaned_df = st.session_state["cleaned_df"]
                    cleaning_report = st.session_state["cleaning_report"]
                    summary = st.session_state["cleaning_summary"]

                    st.subheader("8. Cleaning Summary")

                    a, b, c, d = st.columns(4)

                    a.metric("Original Rows", summary["original_rows"])
                    b.metric("Cleaned Rows", summary["cleaned_rows"])
                    c.metric(
                        "Duplicates Removed",
                        summary["duplicates_removed"]
                    )
                    d.metric(
                        "Missing Cells Remaining",
                        summary["final_missing"]
                    )

                    st.subheader("9. Cleaning Operations Report")

                    st.dataframe(
                        cleaning_report,
                        use_container_width=True
                    )

                    st.subheader("10. Cleaned Data Preview")

                    st.dataframe(
                        cleaned_df.head(100),
                        use_container_width=True
                    )

                    st.download_button(
                        "Download Cleaned CSV",
                        data=dataframe_to_csv(cleaned_df),
                        file_name="cleaned_data.csv",
                        mime="text/csv",
                        key="preparation_cleaned_csv"
                    )

                    # PHASE 4 - VALIDATION

                    st.divider()

                    st.header("11. Data Validation Engine")

                    st.write(
                        "Select validation rules for your cleaned dataset."
                    )

                    columns = cleaned_df.columns.tolist()

                    required_columns = st.multiselect(
                        "Select required columns",
                        columns,
                        key="required_validation"
                    )

                    unique_columns = st.multiselect(
                        "Select primary key / unique columns",
                        columns,
                        key="unique_validation"
                    )

                    email_columns = st.multiselect(
                        "Select email columns",
                        columns,
                        key="email_validation"
                    )

                    phone_columns = st.multiselect(
                        "Select phone number columns",
                        columns,
                        key="phone_validation"
                    )

                    numeric_columns = st.multiselect(
                        "Select numeric columns",
                        columns,
                        key="numeric_validation"
                    )

                    date_columns = st.multiselect(
                        "Select date columns",
                        columns,
                        key="date_validation"
                    )

                    if st.button(
                        "Run Data Validation",
                        type="primary"
                    ):

                        valid_df, rejected_df, validation_report = (
                            validate_dataframe(
                                cleaned_df,
                                required_columns=required_columns,
                                unique_columns=unique_columns,
                                email_columns=email_columns,
                                phone_columns=phone_columns,
                                numeric_columns=numeric_columns,
                                date_columns=date_columns
                            )
                        )

                        st.session_state["valid_df"] = valid_df
                        st.session_state["rejected_df"] = rejected_df
                        st.session_state["validation_report"] = (
                            validation_report
                        )
                        st.session_state["validation_source"] = file_hash

                        st.success("Data validation completed!")

                    # DISPLAY VALIDATION RESULTS

                    if (
                        "valid_df" in st.session_state
                        and st.session_state.get("validation_source")
                        == file_hash
                    ):

                        valid_df = st.session_state["valid_df"]
                        rejected_df = st.session_state["rejected_df"]
                        validation_report = st.session_state[
                            "validation_report"
                        ]

                        st.subheader("12. Validation Summary")

                        v1, v2, v3 = st.columns(3)

                        v1.metric("Total Records", len(cleaned_df))
                        v2.metric("Valid Records", len(valid_df))
                        v3.metric("Rejected Records", len(rejected_df))

                        st.subheader("Validation Report")

                        st.dataframe(
                            validation_report,
                            use_container_width=True
                        )

                        st.subheader("13. Valid Records")

                        st.dataframe(
                            valid_df.head(100),
                            use_container_width=True
                        )

                        st.download_button(
                            "Download Valid Records",
                            data=dataframe_to_csv(valid_df),
                            file_name="valid_records.csv",
                            mime="text/csv",
                            key="preparation_valid_csv"
                        )

                        st.subheader(
                            "14. Rejected Records and Error Details"
                        )

                        if not rejected_df.empty:

                            st.dataframe(
                                rejected_df,
                                use_container_width=True
                            )

                            st.download_button(
                                "Download Rejected Records",
                                data=dataframe_to_csv(rejected_df),
                                file_name="rejected_records.csv",
                                mime="text/csv",
                                key="preparation_rejected_csv"
                            )

                        else:
                            st.success(
                                "Excellent! No rejected records found."
                            )

            # ==========================================
            # PAGE 2: COMPLETE ETL PIPELINE
            # ==========================================

            elif selected_page == "Complete ETL Pipeline":

                st.subheader("1. Input Data Summary")

                c1, c2, c3 = st.columns(3)

                c1.metric("Input File", uploaded_file.name)
                c2.metric("Total Input Rows", f"{len(df):,}")
                c3.metric("Total Columns", len(df.columns))

                st.subheader("2. Configure ETL Pipeline")

                st.write("Data Cleaning Options")

                col1, col2, col3 = st.columns(3)

                with col1:
                    remove_duplicates = st.checkbox(
                        "Remove duplicate rows",
                        value=True,
                        key="pipeline_duplicates"
                    )

                with col2:
                    trim_whitespace = st.checkbox(
                        "Trim whitespace",
                        value=True,
                        key="pipeline_trim"
                    )

                with col3:
                    fill_missing = st.checkbox(
                        "Fill missing values",
                        value=False,
                        key="pipeline_fill"
                    )

                if fill_missing:
                    st.warning(
                        "Numeric missing values use median; "
                        "text missing values use mode."
                    )

                st.divider()

                st.write("Data Validation Rules")

                columns = df.columns.tolist()

                required_columns = st.multiselect(
                    "Required columns",
                    columns,
                    key="pipeline_required"
                )

                unique_columns = st.multiselect(
                    "Unique / Primary Key columns",
                    columns,
                    key="pipeline_unique"
                )

                email_columns = st.multiselect(
                    "Email columns",
                    columns,
                    key="pipeline_email"
                )

                phone_columns = st.multiselect(
                    "Phone number columns",
                    columns,
                    key="pipeline_phone"
                )

                numeric_columns = st.multiselect(
                    "Numeric columns",
                    columns,
                    key="pipeline_numeric"
                )

                date_columns = st.multiselect(
                    "Date columns",
                    columns,
                    key="pipeline_date"
                )

                st.divider()

                st.subheader("3. Execute Complete ETL")

                st.write(
                    "The pipeline will extract the uploaded file, "
                    "clean the data, validate records and prepare "
                    "downloadable outputs."
                )

                if st.button(
                    "🚀 Run Complete ETL Pipeline",
                    type="primary",
                    use_container_width=True
                ):

                    with st.spinner(
                        "Executing ETL pipeline. Please wait..."
                    ):

                        result = run_etl_pipeline(
                            df,
                            remove_duplicates=remove_duplicates,
                            trim_whitespace=trim_whitespace,
                            fill_missing=fill_missing,
                            required_columns=required_columns,
                            unique_columns=unique_columns,
                            email_columns=email_columns,
                            phone_columns=phone_columns,
                            numeric_columns=numeric_columns,
                            date_columns=date_columns
                        )

                    st.session_state["pipeline_result"] = result
                    st.session_state["pipeline_source"] = file_hash
                    try:
                        save_etl_history(uploaded_file.name, result["summary"])
                        st.success("ETL execution history saved successfully!")
                    except Exception as history_error:
                        st.warning(f"Pipeline completed, but history could not be saved: {history_error}")
            
                    st.success(
                        "Complete ETL Pipeline executed successfully!"
                    )

                # DISPLAY PIPELINE RESULTS

                if (
                    "pipeline_result" in st.session_state
                    and st.session_state.get("pipeline_source")
                    == file_hash
                ):

                    result = st.session_state["pipeline_result"]

                    cleaned_df = result["cleaned_df"]
                    valid_df = result["valid_df"]
                    rejected_df = result["rejected_df"]

                    cleaning_report = result["cleaning_report"]
                    validation_report = result["validation_report"]
                    summary = result["summary"]

                    st.divider()

                    st.subheader("4. ETL Execution Summary")

                    m1, m2, m3, m4 = st.columns(4)

                    m1.metric(
                        "Input Rows",
                        f"{summary['total_input_rows']:,}"
                    )

                    m2.metric(
                        "Cleaned Rows",
                        f"{summary['cleaned_rows']:,}"
                    )

                    m3.metric(
                        "Valid Records",
                        f"{summary['valid_records']:,}"
                    )

                    m4.metric(
                        "Rejected Records",
                        f"{summary['rejected_records']:,}"
                    )

                    m5, m6, m7 = st.columns(3)

                    m5.metric(
                        "Duplicates Removed",
                        summary["duplicates_removed"]
                    )

                    m6.metric(
                        "Missing Cells Filled",
                        summary["missing_cells_filled"]
                    )

                    m7.metric(
                        "Execution Time",
                        f"{summary['execution_time_seconds']} sec"
                    )

                    st.success(
                        f"Pipeline Status: {summary['pipeline_status']}"
                    )

                    # CLEANING REPORT

                    st.subheader("5. Cleaning Report")

                    st.dataframe(
                        cleaning_report,
                        use_container_width=True
                    )

                    # VALIDATION REPORT

                    st.subheader("6. Validation Report")

                    st.dataframe(
                        validation_report,
                        use_container_width=True
                    )

                    # CLEANED DATA

                    st.subheader("7. Cleaned Data")

                    st.dataframe(
                        cleaned_df.head(100),
                        use_container_width=True
                    )

                    # VALID RECORDS

                    st.subheader("8. Valid Records")

                    st.dataframe(
                        valid_df.head(100),
                        use_container_width=True
                    )

                    # REJECTED RECORDS

                    st.subheader("9. Rejected Records")

                    if not rejected_df.empty:

                        st.dataframe(
                            rejected_df.head(100),
                            use_container_width=True
                        )

                    else:

                        st.success(
                            "No rejected records found."
                        )

                    # DOWNLOAD SECTION

                    st.divider()

                    st.header("10. Download ETL Results")

                    d1, d2 = st.columns(2)

                    with d1:

                        st.download_button(
                            "Download Cleaned CSV",
                            data=dataframe_to_csv(cleaned_df),
                            file_name="cleaned_data.csv",
                            mime="text/csv",
                            key="pipeline_cleaned_csv"
                        )

                        st.download_button(
                            "Download Valid Records CSV",
                            data=dataframe_to_csv(valid_df),
                            file_name="valid_records.csv",
                            mime="text/csv",
                            key="pipeline_valid_csv"
                        )

                        st.download_button(
                            "Download Rejected Records CSV",
                            data=dataframe_to_csv(rejected_df),
                            file_name="rejected_records.csv",
                            mime="text/csv",
                            key="pipeline_rejected_csv"
                        )

                    with d2:

                        st.download_button(
                            "Download Cleaned Excel",
                            data=dataframe_to_excel(
                                cleaned_df,
                                "Cleaned_Data"
                            ),
                            file_name="cleaned_data.xlsx",
                            mime=(
                                "application/vnd.openxmlformats-officedocument."
                                "spreadsheetml.sheet"
                            ),
                            key="pipeline_cleaned_excel"
                        )

                        excel_report = create_etl_excel_report(
                            cleaned_df=cleaned_df,
                            valid_df=valid_df,
                            rejected_df=rejected_df,
                            cleaning_report=cleaning_report,
                            validation_report=validation_report,
                            summary=summary
                        )

                        st.download_button(
                            "📥 Download Complete ETL Excel Report",
                            data=excel_report,
                            file_name="SmartETL_Complete_Report.xlsx",
                            mime=(
                                "application/vnd.openxmlformats-officedocument."
                                "spreadsheetml.sheet"
                            ),
                            key="pipeline_complete_excel",
                            use_container_width=True
                        )

        except Exception as error:

            st.error(
                f"Data processing failed: {str(error)}"
            )

    else:

        st.info(
            "Upload a CSV, Excel or JSON file to start."
        )
        
# --------------------------------------------------
# ETL DASHBOARD - PHASE 6
# --------------------------------------------------

elif selected_page == "ETL Dashboard":

    st.title("📊 ETL Execution Dashboard")
    st.caption("Monitor ETL pipeline performance and execution history.")

    history_df = load_etl_history()

    if history_df.empty:

        st.info("No ETL execution history available. Run your ETL pipeline first.")

    else:

        summary = get_etl_history_summary()

        # KPI METRICS
        st.subheader("1. Pipeline Overview")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total Runs", summary["total_runs"])
        col2.metric("Total Records", f'{summary["total_records"]:,}')
        col3.metric("Valid Records", f'{summary["total_valid"]:,}')
        col4.metric("Rejected Records", f'{summary["total_rejected"]:,}')

        st.divider()

        # EXECUTION PERFORMANCE
        st.subheader("2. Execution Performance")

        st.metric(
            "Average Execution Time",
            f'{summary["average_execution_time"]} seconds'
        )

        st.line_chart(
            history_df.set_index("Execution Date")[
                ["Execution Time (Seconds)"]
            ]
        )

        st.divider()

        # VALID VS REJECTED
        st.subheader("3. Valid vs Rejected Records")

        st.bar_chart(
            history_df.set_index("Execution Date")[
                ["Valid Records", "Rejected Records"]
            ]
        )

        st.divider()

        # EXECUTION HISTORY
        st.subheader("4. Execution History")

        st.dataframe(
            history_df,
            use_container_width=True,
            hide_index=True
        )

        # DOWNLOAD HISTORY
        st.subheader("5. Export History")

        history_csv = history_df.to_csv(
            index=False
        ).encode("utf-8-sig")

        st.download_button(
            label="📥 Download Execution History",
            data=history_csv,
            file_name="etl_execution_history.csv",
            mime="text/csv"
        )

