
import streamlit as st

from modules.file_reader import read_uploaded_file
from modules.profiler import profile_dataframe
from modules.cleaner import clean_dataframe
from modules.validator import validate_dataframe


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

st.sidebar.title("SmartETL Settings")
st.sidebar.info("Phase 2, 3 & 4: Upload, Cleaning and Validation")

MAX_FILE_SIZE_MB = 50


# --------------------------------------------------
# FILE UPLOAD
# --------------------------------------------------

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

        # --------------------------------------------------
        # PHASE 2 - FILE INFORMATION
        # --------------------------------------------------

        st.subheader("1. File Information")

        col1, col2, col3 = st.columns(3)

        col1.metric("File Name", uploaded_file.name)
        col2.metric("Rows", f"{len(df):,}")
        col3.metric("Columns", len(df.columns))

        # --------------------------------------------------
        # DATA PREVIEW
        # --------------------------------------------------

        st.subheader("2. Data Preview")

        st.dataframe(
            df.head(100),
            use_container_width=True
        )

        # --------------------------------------------------
        # DATA PROFILING
        # --------------------------------------------------

        st.subheader("3. Data Quality Profile")

        profile = profile_dataframe(df)

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Total Records", f"{profile['row_count']:,}")
        c2.metric("Duplicate Rows", f"{profile['duplicate_rows']:,}")
        c3.metric("Missing Cells", f"{profile['null_cells']:,}")
        c4.metric("Completeness", f"{profile['completeness']}%")

        # COLUMN ANALYSIS

        st.subheader("4. Column-Level Analysis")

        st.dataframe(
            profile["columns"],
            use_container_width=True
        )

        # STATISTICS

        st.subheader("5. Descriptive Statistics")

        with st.expander("View statistical analysis"):

            try:

                st.dataframe(
                    df.describe(include="all").transpose(),
                    use_container_width=True
                )

            except Exception:

                st.info(
                    "Statistical analysis is unavailable for this dataset."
                )

        # NULL ANALYSIS

        st.subheader("6. Missing Value Analysis")

        null_summary = profile["columns"][
            ["Column", "Null Count", "Null %"]
        ]

        st.dataframe(
            null_summary,
            use_container_width=True
        )

        st.success("Data profiling completed successfully!")

        # --------------------------------------------------
        # PHASE 3 - DATA CLEANING
        # --------------------------------------------------

        st.divider()

        st.header("7. Data Cleaning")

        st.write(
            "Select the cleaning operations you want to apply."
        )

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
                "Numeric values use median and text values use "
                "the most frequent value. Review the results."
            )

        if st.button(
            "Run Data Cleaning",
            type="primary"
        ):

            cleaned_df, cleaning_report, summary = clean_dataframe(
                df,
                remove_duplicates=remove_duplicates,
                trim_whitespace=trim_whitespace,
                fill_missing=fill_missing
            )

            st.session_state["cleaned_df"] = cleaned_df
            st.session_state["cleaning_report"] = cleaning_report
            st.session_state["cleaning_summary"] = summary
            st.session_state["source_filename"] = uploaded_file.name

            # Clear old validation results after new cleaning
            for key in [
                "valid_df",
                "rejected_df",
                "validation_report",
                "validation_source"
            ]:
                st.session_state.pop(key, None)

            st.success("Data cleaning completed successfully!")

        # --------------------------------------------------
        # DISPLAY CLEANING RESULTS
        # --------------------------------------------------

        if (
            "cleaned_df" in st.session_state
            and st.session_state.get("source_filename")
            == uploaded_file.name
        ):

            cleaned_df = st.session_state["cleaned_df"]
            cleaning_report = st.session_state["cleaning_report"]
            summary = st.session_state["cleaning_summary"]

            st.subheader("8. Cleaning Summary")

            a, b, c, d = st.columns(4)

            a.metric("Original Rows", summary["original_rows"])
            b.metric("Cleaned Rows", summary["cleaned_rows"])
            c.metric("Duplicates Removed", summary["duplicates_removed"])
            d.metric("Missing Cells Remaining", summary["final_missing"])

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

            cleaned_csv = cleaned_df.to_csv(
                index=False
            ).encode("utf-8-sig")

            st.download_button(
                "Download Cleaned CSV",
                data=cleaned_csv,
                file_name="cleaned_data.csv",
                mime="text/csv"
            )

            # --------------------------------------------------
            # PHASE 4 - DATA VALIDATION
            # --------------------------------------------------

            st.divider()

            st.header("11. Data Validation Engine")

            st.write(
                "Select the validation rules for your cleaned dataset."
            )

            columns = cleaned_df.columns.tolist()

            required_columns = st.multiselect(
                "Select required columns",
                options=columns,
                key="required_validation"
            )

            unique_columns = st.multiselect(
                "Select primary key / unique columns",
                options=columns,
                key="unique_validation"
            )

            email_columns = st.multiselect(
                "Select email columns",
                options=columns,
                key="email_validation"
            )

            phone_columns = st.multiselect(
                "Select phone number columns",
                options=columns,
                key="phone_validation"
            )

            numeric_columns = st.multiselect(
                "Select columns that must contain numbers",
                options=columns,
                key="numeric_validation"
            )

            date_columns = st.multiselect(
                "Select columns that must contain valid dates",
                options=columns,
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
                st.session_state["validation_report"] = validation_report
                st.session_state["validation_source"] = uploaded_file.name

                st.success("Data validation completed successfully!")

            # --------------------------------------------------
            # DISPLAY VALIDATION RESULTS
            # --------------------------------------------------

            if (
                "valid_df" in st.session_state
                and st.session_state.get("validation_source")
                == uploaded_file.name
            ):

                valid_df = st.session_state["valid_df"]
                rejected_df = st.session_state["rejected_df"]
                validation_report = st.session_state["validation_report"]

                st.subheader("12. Validation Summary")

                v1, v2, v3 = st.columns(3)

                v1.metric("Total Records", len(cleaned_df))
                v2.metric("Valid Records", len(valid_df))
                v3.metric("Rejected Records", len(rejected_df))

                st.dataframe(
                    validation_report,
                    use_container_width=True
                )

                # VALID RECORDS

                st.subheader("13. Valid Records")

                st.dataframe(
                    valid_df.head(100),
                    use_container_width=True
                )

                st.download_button(
                    "Download Valid Records",
                    data=valid_df.to_csv(
                        index=False
                    ).encode("utf-8-sig"),
                    file_name="valid_records.csv",
                    mime="text/csv"
                )

                # REJECTED RECORDS

                st.subheader("14. Rejected Records and Error Details")

                if not rejected_df.empty:

                    st.dataframe(
                        rejected_df,
                        use_container_width=True
                    )

                    st.download_button(
                        "Download Rejected Records",
                        data=rejected_df.to_csv(
                            index=False
                        ).encode("utf-8-sig"),
                        file_name="rejected_records.csv",
                        mime="text/csv"
                    )

                else:

                    st.success(
                        "Excellent! No rejected records were found."
                    )

    except Exception as error:

        st.error(
            f"Data processing failed: {str(error)}"
        )

else:

    st.info("Upload a CSV, Excel or JSON file to start your ETL process.")
