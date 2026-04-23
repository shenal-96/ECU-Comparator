"""Streamlit app for comparing ECU parameter files (XLS/CSV)."""

import streamlit as st
import pandas as pd
import tempfile
from pathlib import Path
from parser import parse_file
from csv_parser import parse_csv_file
from multi_file_comparator import compare_all_files
from csv_comparator import compare_csv_files


st.set_page_config(page_title="ECU Comparator", layout="wide")
st.title("ECU Parameter File Comparator")

with st.sidebar:
    st.header("Upload Files")

    uploaded_files = st.file_uploader(
        "Select .XLS, .XLSX, or .CSV files to compare",
        type=["xls", "xlsx", "csv"],
        accept_multiple_files=True,
        help="Upload 2 or more ECU parameter files (mix of XLS and CSV allowed)"
    )

    if uploaded_files:
        st.info(f"✓ {len(uploaded_files)} file(s) uploaded")
        run_button = st.button("Run Comparison", key="run", type="primary", use_container_width=True)
    else:
        st.warning("Please upload at least 2 files to compare")
        run_button = False

st.divider()

if run_button and uploaded_files and len(uploaded_files) >= 2:
    with st.spinner("Loading and comparing files..."):
        try:
            files_data = {}
            file_types = {}

            with tempfile.TemporaryDirectory() as tmpdir:
                for uploaded_file in uploaded_files:
                    temp_path = Path(tmpdir) / uploaded_file.name
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    file_label = Path(uploaded_file.name).stem
                    file_ext = Path(uploaded_file.name).suffix.lower()

                    if file_ext == ".csv":
                        files_data[file_label] = parse_csv_file(str(temp_path))
                        file_types[file_label] = "csv"
                    else:
                        files_data[file_label] = parse_file(str(temp_path))
                        file_types[file_label] = "xls"

                # Separate by type and compare
                csv_files = {k: v for k, v in files_data.items() if file_types[k] == "csv"}
                xls_files = {k: v for k, v in files_data.items() if file_types[k] == "xls"}

                all_diffs = []

                if csv_files and len(csv_files) >= 2:
                    csv_diffs = compare_csv_files(csv_files)
                    all_diffs.extend(csv_diffs)

                if xls_files and len(xls_files) >= 2:
                    xls_diffs = compare_all_files(xls_files)
                    all_diffs.extend(xls_diffs)

                if all_diffs:
                    df = pd.DataFrame(all_diffs)

                    st.success(f"✓ Found **{len(df)}** difference locations across **{len(uploaded_files)}** files")

                    # Build filter options based on available columns
                    filter_cols = [col for col in df.columns if col in ["Sheet", "Group"]]

                    if filter_cols:
                        filter_options = []
                        filter_col = filter_cols[0]

                        if filter_col == "Sheet":
                            filter_options = df["Sheet"].unique().tolist()
                        elif filter_col == "Group":
                            filter_options = df["Group"].unique().tolist()

                        if filter_options:
                            selected_filters = st.multiselect(
                                f"Filter by {filter_col}",
                                filter_options,
                                default=filter_options,
                            )
                            filtered_df = df[df[filter_col].isin(selected_filters)].copy()
                        else:
                            filtered_df = df.copy()
                    else:
                        filtered_df = df.copy()

                    st.subheader(f"Differences ({len(filtered_df)} locations)")

                    # Get file columns (exclude structural columns)
                    exclude_cols = {"Sheet", "Nr", "Name", "Location", "Group", "Sub-group", "Dimension"}
                    file_cols = [col for col in filtered_df.columns if col not in exclude_cols]

                    # Build column config dynamically
                    col_config = {}
                    for col in filtered_df.columns:
                        if col in exclude_cols:
                            col_config[col] = st.column_config.TextColumn(width="small")
                        else:
                            # Try to display as number if possible
                            try:
                                pd.to_numeric(filtered_df[col], errors="coerce")
                                col_config[col] = st.column_config.TextColumn(width="small")
                            except:
                                col_config[col] = st.column_config.TextColumn(width="small")

                    st.dataframe(
                        filtered_df,
                        use_container_width=True,
                        hide_index=True,
                        column_config=col_config
                    )

                    csv = filtered_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download as CSV",
                        data=csv,
                        file_name="ecu_differences.csv",
                        mime="text/csv",
                    )

                else:
                    st.info("No differences found! All files are identical.")

        except Exception as e:
            st.error(f"Error during comparison: {str(e)}")

elif not run_button:
    st.info("👈 Select files in the sidebar and click 'Run Comparison' to begin.")
