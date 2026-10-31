
import streamlit as st

from modules.file_reader import read_uploaded_file
from modules.profiler import profile_dataframe

st.set_page_config(
    page_title="SmartETL AI",
    page_icon="🧹",
    layout="wide"
)

st.title("🧹 SmartETL AI")
st.caption("Intelligent ETL and Data Quality Platform")

st.sidebar.title("SmartETL Settings")
st.sidebar.info("Phase 2: Upload & Data Profiling")

MAX_FILE_SIZE_MB = 50

uploaded_file = st.file_uploader(
    "Upload your dataset",
    type=["csv", "xlsx", "xls", "json"]
)

if uploaded_file:

    if uploaded_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        st.error("File exceeds the 50 MB limit.")
        st.stop()

    try:

        df = read_uploaded_file(uploaded_file)

        if df.empty:
            st.warning("Uploaded file contains no records.")
            st.stop()

        if df.columns.duplicated().any():
            st.error("Duplicate column names detected.")
            st.stop()

        st.success("File uploaded successfully!")

        # 1. File information
        st.subheader("1. File Information")

        col1, col2, col3 = st.columns(3)

        col1.metric("File Name", uploaded_file.name)
        col2.metric("Rows", f"{len(df):,}")
        col3.metric("Columns", len(df.columns))

        # 2. Data preview
        st.subheader("2. Data Preview")

        st.dataframe(
            df.head(100),
            use_container_width=True
        )

        # 3. Data profiling
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

        # 4. Column-level analysis
        st.subheader("4. Column-Level Analysis")

        st.dataframe(
            profile["columns"],
            use_container_width=True
        )

        # 5. Descriptive statistics
        st.subheader("5. Descriptive Statistics")

        with st.expander("View statistical analysis"):

            st.dataframe(
                df.describe(include="all").transpose(),
                use_container_width=True
            )

        # 6. Null analysis
        st.subheader("6. Missing Value Analysis")

        null_summary = profile["columns"][
            ["Column", "Null Count", "Null %"]
        ]

        st.dataframe(
            null_summary,
            use_container_width=True
        )

        st.success(
            "Data profiling completed successfully!"
        )

    except Exception as error:

        st.error(
            f"Data processing failed: {str(error)}"
        )
