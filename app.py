
import streamlit as st
import hashlib

from modules.auth import (
    initialize_auth_db,
    authenticate_user,
    create_user,
    list_users,
    set_user_active
)

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
from modules.quality_report import generate_quality_report
from modules.database import (
    test_database_connection,
    load_valid_records
)
from modules.database_import import (
    create_database_engine,
    test_import_connection,
    get_database_schemas,
    get_database_tables,
    import_database_table,
    import_sql_query
)
from modules.quality_report import generate_quality_report
from modules.gemini_report import (
    gemini_is_configured,
    generate_gemini_quality_report
)


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="SmartETL AI",
    page_icon="🧹",
    layout="wide"
)


# --------------------------------------------------
# AUTHENTICATION - PRIVATE APPLICATION ACCESS
# --------------------------------------------------

try:
    initialize_auth_db()
except Exception as auth_error:
    st.error("SmartETL AI authentication setup failed.")
    st.error(str(auth_error))
    st.info(
        "Check ADMIN_USERNAME and ADMIN_PASSWORD in your local .env file. "
        "Do not share your .env file or credentials."
    )
    st.stop()

if "authenticated_user" not in st.session_state:
    st.session_state["authenticated_user"] = None

if not st.session_state["authenticated_user"]:
    st.title("🔐 SmartETL AI")
    st.subheader("Sign in to your account")
    st.caption("Private access. Contact the administrator if you need an account.")

    with st.form("smartetl_login_form"):
        login_username = st.text_input("Username")
        login_password = st.text_input("Password", type="password")
        login_submitted = st.form_submit_button(
            "Login",
            type="primary",
            use_container_width=True
        )

    if login_submitted:
        logged_in_user = authenticate_user(
            login_username,
            login_password
        )

        if logged_in_user:
            st.session_state["authenticated_user"] = logged_in_user
            st.rerun()
        else:
            st.error("Invalid username or password, or the account is inactive.")

    st.stop()

current_user = st.session_state["authenticated_user"]

# Prevent data from a previous login being reused after an account switch.
if st.session_state.get("_session_user_id") != current_user["id"]:
    st.session_state.clear()
    st.session_state["authenticated_user"] = current_user
    st.session_state["_session_user_id"] = current_user["id"]
    st.rerun()

st.title("🧹 SmartETL AI")
st.caption("Intelligent ETL and Data Quality Platform")


# --------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------

st.sidebar.title("SmartETL AI")
st.sidebar.caption("Data Engineering Platform")
st.sidebar.write(f"Signed in: **{current_user['username']}**")
st.sidebar.caption(f"Role: {current_user['role'].title()}")

if st.sidebar.button("Logout", use_container_width=True):
    # Release a database engine if one was opened during this session.
    source_engine = st.session_state.get("source_db_engine")
    if source_engine is not None:
        try:
            source_engine.dispose()
        except Exception:
            pass

    # Remove uploaded data, ETL results, reports and widget state.
    st.session_state.clear()
    st.rerun()

navigation_pages = [
    "Home",
    "Data Preparation",
    "Complete ETL Pipeline",
    "Database Import",
    "ETL Dashboard"
]

if current_user["role"] == "admin":
    navigation_pages.append("User Management")

selected_page = st.sidebar.radio(
    "Navigation",
    navigation_pages
)

st.sidebar.divider()
st.sidebar.info("Private SmartETL AI workspace")

MAX_FILE_SIZE_MB = 50


# --------------------------------------------------
# ADMIN - USER MANAGEMENT
# --------------------------------------------------

if selected_page == "User Management":

    if current_user["role"] != "admin":
        st.error("You are not authorized to access this page.")
        st.stop()

    st.header("👥 User Management")
    st.caption("Only the administrator can create and manage user accounts.")

    st.subheader("Create a New User")

    with st.form("create_smartetl_user_form"):
        new_username = st.text_input(
            "Username",
            help="Use 3–32 letters, numbers, underscores or hyphens."
        )
        new_password = st.text_input(
            "Temporary password",
            type="password",
            help="Use at least 12 characters."
        )
        confirm_password = st.text_input(
            "Confirm temporary password",
            type="password"
        )
        create_user_submitted = st.form_submit_button(
            "Create User",
            type="primary"
        )

    if create_user_submitted:
        if new_password != confirm_password:
            st.error("The passwords do not match.")
        else:
            try:
                create_user(new_username, new_password)
                st.success(
                    f"User '{new_username.strip().lower()}' created successfully. "
                    "Share the credentials with that user through a secure channel."
                )
            except ValueError as user_error:
                st.error(str(user_error))
            except Exception as user_error:
                st.error(f"Could not create user: {user_error}")

    st.divider()
    st.subheader("Existing Accounts")

    users = list_users()

    if users:
        for user in users:
            user_col, role_col, status_col, action_col = st.columns(
                [3, 1.5, 1.5, 2]
            )

            user_col.write(f"**{user['username']}**")
            role_col.write(user["role"].title())
            status_col.write(
                "Active" if user["is_active"] else "Inactive"
            )

            if user["role"] == "user":
                if user["is_active"]:
                    if action_col.button(
                        "Deactivate",
                        key=f"deactivate_user_{user['id']}"
                    ):
                        set_user_active(user["id"], False)
                        st.rerun()
                else:
                    if action_col.button(
                        "Activate",
                        key=f"activate_user_{user['id']}"
                    ):
                        set_user_active(user["id"], True)
                        st.rerun()
            else:
                action_col.caption("Protected admin account")
    else:
        st.info("No user accounts have been created yet.")


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

elif selected_page == "Home":

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
                        save_etl_history(
                            current_user["id"], uploaded_file.name, result["summary"])
                        st.success("ETL execution history saved successfully!")
                    except Exception as history_error:
                        st.warning(
                            f"Pipeline completed, but history could not be saved: {history_error}")
                    # Generate Data Quality Report
                    quality_report = generate_quality_report(df, result)
                    st.session_state["quality_report"] = quality_report
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
                    # DATA QUALITY ANALYSIS

                    st.divider()
                    st.header("🤖 Data Quality Analysis")

                    quality_report = st.session_state.get("quality_report")

                    if quality_report:

                        col1, col2, col3, col4 = st.columns(4)

                        col1.metric(
                            "Quality Score",
                            f"{quality_report['quality_score']}%"
                        )

                        col2.metric(
                            "Quality Grade",
                            quality_report["grade"]
                        )

                        col3.metric(
                            "Completeness",
                            f"{quality_report['completeness']}%"
                        )

                        col4.metric(
                            "Validity",
                            f"{quality_report['validity']}%"
                        )

                        st.progress(quality_report["quality_score"] / 100)

                        st.subheader("Identified Issues")

                        for issue in quality_report["issues"]:
                            st.warning(issue)

                        st.subheader("Recommendations")

                        for recommendation in quality_report["recommendations"]:
                            st.info(recommendation)

                        st.download_button(
                            "Download Data Quality Report",
                            data=quality_report["report_text"],
                            file_name="SmartETL_Data_Quality_Report.txt",
                            mime="text/plain",
                            key="quality_report_download"
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

                    # SQL SERVER DATABASE INTEGRATION

                    st.divider()
                    st.header("11. SQL Server Database Integration")

                    st.write(
                        "Test your SQL Server connection and load "
                        "validated records into the SmartETL_AI database."
                    )

                    if st.button(
                        "Test SQL Server Connection",
                        key="test_sql_server_connection"
                    ):
                        try:
                            database_name = test_database_connection()

                            st.success(
                                f"Connected successfully to database: {database_name}"
                            )

                        except Exception as error:
                            st.error(f"Connection failed: {error}")

                    if not valid_df.empty:

                        st.info(
                            f"{len(valid_df):,} validated records are ready for database loading."
                        )

                        if st.button(
                            "Load Valid Records into SQL Server",
                            type="primary",
                            key="load_sql_server_records"
                        ):

                            try:
                                with st.spinner("Loading records into SQL Server..."):

                                    load_result = load_valid_records(
                                        valid_df,
                                        uploaded_file.name
                                    )

                                    st.session_state["sql_load_result"] = {
                                        "source": file_hash,
                                        **load_result
                                    }

                            except Exception as error:
                                st.error(f"SQL Server load failed: {error}")

                    # DISPLAY DATABASE LOAD RESULT

                    sql_result = st.session_state.get("sql_load_result")

                    if sql_result and sql_result.get("source") == file_hash:

                        st.subheader("SQL Server Load Summary")

                        db1, db2, db3 = st.columns(3)

                        db1.metric(
                            "Total Records",
                            sql_result["total_records"]
                        )

                        db2.metric(
                            "Successfully Loaded",
                            sql_result["successful_records"]
                        )

                        db3.metric(
                            "Failed Records",
                            sql_result["failed_records"]
                        )

                        st.success(
                            f"Database Load Status: {sql_result['status']}"
                        )

                        st.code(
                            f"Batch ID: {sql_result['batch_id']}"
                        )

                    else:
                        if valid_df.empty:
                            st.warning(
                                "No valid records available for database loading.")

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
# DATABASE IMPORT - SOURCE DATABASE CONNECTIVITY
# --------------------------------------------------

elif selected_page == "Database Import":

    st.header("Database Import")
    st.caption("Connect to a relational database, select a table or run a read-only SQL query, and import the result into SmartETL AI.")

    st.info("Use a read-only database account where possible. Connection details are used for this Streamlit session and are not saved by this page.")

    db_type = st.selectbox(
        "Select Database",
        ["SQL Server", "MySQL", "PostgreSQL", "SQLite"],
        key="source_db_type"
    )

    with st.form("source_database_connection_form"):
        if db_type == "SQLite":
            sqlite_path = st.text_input(
                "SQLite database file path",
                placeholder=r"D:\Data\source_database.db"
            )
            host = port = database = username = password = None
            windows_auth = False
            driver = "ODBC Driver 18 for SQL Server"
        else:
            c1, c2 = st.columns(2)
            with c1:
                host = st.text_input("Server / Host", value="localhost")
                if db_type == "SQL Server":
                    port = st.text_input("Port (optional)", placeholder="1433")
                elif db_type == "MySQL":
                    port = st.text_input("Port", value="3306")
                else:
                    port = st.text_input("Port", value="5432")
                database = st.text_input("Database name")
            with c2:
                if db_type == "SQL Server":
                    windows_auth = st.checkbox(
                        "Use Windows Authentication", value=True)
                    driver = st.selectbox(
                        "ODBC Driver",
                        ["ODBC Driver 18 for SQL Server",
                            "ODBC Driver 17 for SQL Server"]
                    )
                else:
                    windows_auth = False
                    driver = "ODBC Driver 18 for SQL Server"
                username = st.text_input("Username", disabled=windows_auth)
                password = st.text_input(
                    "Password", type="password", disabled=windows_auth)
            sqlite_path = None

        connect_clicked = st.form_submit_button(
            "Test Connection", type="primary")

    if connect_clicked:
        try:
            engine = create_database_engine(
                database_type=db_type,
                host=host,
                port=port,
                database=database,
                username=username,
                password=password,
                windows_auth=windows_auth,
                driver=driver,
                sqlite_path=sqlite_path,
            )
            test_import_connection(engine)
            st.session_state["source_db_engine"] = engine
            st.session_state["source_db_type_connected"] = db_type
            st.session_state.pop("database_import_df", None)
            st.session_state.pop("database_import_source", None)
            st.success(f"Successfully connected to {db_type}.")
        except Exception as error:
            st.error(f"Database connection failed: {error}")

    engine = st.session_state.get("source_db_engine")
    connected_type = st.session_state.get("source_db_type_connected")

    if engine is not None and connected_type == db_type:
        st.divider()
        st.subheader("Import Data")
        import_method = st.radio(
            "Choose import method",
            ["Select a table", "Run a SQL query"],
            horizontal=True,
            key="database_import_method"
        )
        row_limit = st.number_input(
            "Maximum rows to import",
            min_value=1,
            max_value=1000000,
            value=100000,
            step=10000
        )

        if import_method == "Select a table":
            try:
                schemas = get_database_schemas(engine)
                if schemas and schemas != [None]:
                    selected_schema = st.selectbox(
                        "Select schema",
                        schemas,
                        format_func=lambda value: str(value),
                        key="source_db_schema"
                    )
                else:
                    selected_schema = None

                tables = get_database_tables(engine, selected_schema)
                if tables:
                    selected_table = st.selectbox(
                        "Select table",
                        tables,
                        key="source_db_table"
                    )
                    if st.button("Import Selected Table", type="primary"):
                        imported_df, truncated = import_database_table(
                            engine, selected_table, selected_schema, int(
                                row_limit)
                        )
                        st.session_state["database_import_df"] = imported_df
                        st.session_state["database_import_source"] = f"{db_type}: {selected_table}"
                        st.session_state["database_import_truncated"] = truncated
                else:
                    st.warning("No tables were found in this database/schema.")
            except Exception as error:
                st.error(f"Could not retrieve database tables: {error}")

        else:
            sql_query = st.text_area(
                "SQL SELECT query",
                placeholder="SELECT TOP 100 * FROM dbo.Customers; -- SQL Server example\n-- Use LIMIT for MySQL/PostgreSQL/SQLite as appropriate",
                height=160,
                key="database_source_sql_query"
            )
            if st.button("Execute Query and Import", type="primary"):
                try:
                    imported_df, truncated = import_sql_query(
                        engine, sql_query, int(row_limit)
                    )
                    st.session_state["database_import_df"] = imported_df
                    st.session_state["database_import_source"] = f"{db_type}: SQL query"
                    st.session_state["database_import_truncated"] = truncated
                except Exception as error:
                    st.error(f"Query import failed: {error}")

        imported_df = st.session_state.get("database_import_df")
        if imported_df is not None:
            source_label = st.session_state.get(
                "database_import_source", "Database source")
            st.divider()
            st.subheader("Imported Data Preview")
            if st.session_state.get("database_import_truncated"):
                st.warning(
                    f"Preview/import was limited to {len(imported_df):,} rows. Increase the row limit if needed.")
            st.success(
                f"Imported {len(imported_df):,} rows and {len(imported_df.columns):,} columns from {source_label}.")
            st.dataframe(imported_df.head(100), use_container_width=True)

            profile = profile_dataframe(imported_df)
            p1, p2, p3, p4 = st.columns(4)
            p1.metric("Rows", f"{profile['row_count']:,}")
            p2.metric("Columns", profile["column_count"])
            p3.metric("Duplicate Rows", f"{profile['duplicate_rows']:,}")
            p4.metric("Completeness", f"{profile['completeness']}%")
            with st.expander("View imported data column profile"):
                st.dataframe(profile["columns"], use_container_width=True)

            st.divider()
            st.subheader("Run SmartETL AI Pipeline on Imported Data")
            cols = imported_df.columns.tolist()
            with st.form("database_import_etl_form"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    db_remove_duplicates = st.checkbox(
                        "Remove duplicate rows", value=True, key="db_etl_dedupe")
                with c2:
                    db_trim_whitespace = st.checkbox(
                        "Trim whitespace", value=True, key="db_etl_trim")
                with c3:
                    db_fill_missing = st.checkbox(
                        "Fill missing values", value=False, key="db_etl_fill")
                db_required = st.multiselect(
                    "Required columns", cols, key="db_etl_required")
                db_unique = st.multiselect(
                    "Unique / primary key columns", cols, key="db_etl_unique")
                db_email = st.multiselect(
                    "Email columns", cols, key="db_etl_email")
                db_phone = st.multiselect(
                    "Phone columns", cols, key="db_etl_phone")
                db_numeric = st.multiselect(
                    "Numeric columns", cols, key="db_etl_numeric")
                db_dates = st.multiselect(
                    "Date columns", cols, key="db_etl_dates")
                run_database_etl = st.form_submit_button(
                    "Run ETL on Imported Data", type="primary")

            if run_database_etl:
                try:
                    with st.spinner("Running ETL on database records..."):
                        result = run_etl_pipeline(
                            imported_df,
                            remove_duplicates=db_remove_duplicates,
                            trim_whitespace=db_trim_whitespace,
                            fill_missing=db_fill_missing,
                            required_columns=db_required,
                            unique_columns=db_unique,
                            email_columns=db_email,
                            phone_columns=db_phone,
                            numeric_columns=db_numeric,
                            date_columns=db_dates,
                        )
                    st.session_state["database_import_etl_result"] = result
                    st.session_state["database_import_etl_source"] = source_label
                    st.session_state["database_import_quality_report"] = generate_quality_report(
                        imported_df, result)
                    try:
                        save_etl_history(
                            current_user["id"], source_label, result["summary"])
                    except Exception as history_error:
                        st.warning(
                            f"ETL completed, but execution history could not be saved: {history_error}")
                    st.success(
                        "ETL completed successfully for the imported database data.")
                except Exception as error:
                    st.error(f"Database ETL failed: {error}")

            db_result = st.session_state.get("database_import_etl_result")
            if db_result is not None and st.session_state.get("database_import_etl_source") == source_label:
                db_summary = db_result["summary"]
                st.subheader("Database ETL Results")
                r1, r2, r3, r4 = st.columns(4)
                r1.metric("Input Rows", db_summary["total_input_rows"])
                r2.metric("Valid Records", db_summary["valid_records"])
                r3.metric("Rejected Records", db_summary["rejected_records"])
                r4.metric("Execution Time",
                          f"{db_summary['execution_time_seconds']} sec")
                st.subheader("Valid Records")
                st.dataframe(db_result["valid_df"].head(
                    100), use_container_width=True)
                st.subheader("Rejected Records")
                st.dataframe(db_result["rejected_df"].head(
                    100), use_container_width=True)
                st.download_button(
                    "Download Valid Records CSV",
                    data=dataframe_to_csv(db_result["valid_df"]),
                    file_name="database_valid_records.csv",
                    mime="text/csv",
                    key="database_import_valid_download"
                )
                st.download_button(
                    "Download Rejected Records CSV",
                    data=dataframe_to_csv(db_result["rejected_df"]),
                    file_name="database_rejected_records.csv",
                    mime="text/csv",
                    key="database_import_rejected_download"
                )
                db_quality = st.session_state.get(
                    "database_import_quality_report")
                if db_quality:
                    st.subheader("Data Quality Report")
                    st.metric("Quality Score",
                              f"{db_quality['quality_score']}%")
                    st.write("**Recommendations**")
                    for item in db_quality["recommendations"]:
                        st.info(item)


# --------------------------------------------------
# ETL DASHBOARD - PHASE 6
# --------------------------------------------------

elif selected_page == "ETL Dashboard":

    st.title("📊 ETL Execution Dashboard")
    st.caption("Monitor ETL pipeline performance and execution history.")

    history_df = load_etl_history(current_user["id"])

    if history_df.empty:

        st.info("No ETL execution history available. Run your ETL pipeline first.")

    else:

        summary = get_etl_history_summary(current_user["id"])

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
