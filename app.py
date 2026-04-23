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

# Separate file uploaders for XLS and CSV
col1, col2 = st.columns(2)

with col1:
    st.subheader("XLS Files")
    xls_files = st.file_uploader(
        "Select .XLS/.XLSX files",
        type=["xls", "xlsx"],
        accept_multiple_files=True,
        key="xls_uploader",
        help="Upload ECU parameter .XLS files"
    )

with col2:
    st.subheader("CSV Files")
    csv_files = st.file_uploader(
        "Select .CSV files",
        type=["csv"],
        accept_multiple_files=True,
        key="csv_uploader",
        help="Upload ComAp configuration .CSV files"
    )

st.divider()

# Create tabs for each comparison type
tab1, tab2 = st.tabs(["XLS Comparison", "CSV Comparison"])

# XLS COMPARISON TAB
with tab1:
    if xls_files and len(xls_files) >= 2:
        if st.button("Run XLS Comparison", key="xls_run", type="primary", use_container_width=True):
            with st.spinner("Loading and comparing XLS files..."):
                try:
                    files_data = {}
                    with tempfile.TemporaryDirectory() as tmpdir:
                        for uploaded_file in xls_files:
                            temp_path = Path(tmpdir) / uploaded_file.name
                            with open(temp_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())

                            file_label = Path(uploaded_file.name).stem
                            files_data[file_label] = parse_file(str(temp_path))

                        diffs = compare_all_files(files_data)

                        if diffs:
                            df = pd.DataFrame(diffs)

                            st.success(f"✓ Found **{len(df)}** difference locations across **{len(xls_files)}** files")

                            # Filter by sheet
                            sheet_filter = st.multiselect(
                                "Filter by Sheet",
                                ["Parameter", "Val_2D", "Val_3D"],
                                default=["Parameter", "Val_2D", "Val_3D"],
                                key="xls_sheet_filter"
                            )

                            filtered_df = df[df["Sheet"].isin(sheet_filter)].copy()

                            st.subheader(f"Differences ({len(filtered_df)} locations)")

                            # Get file columns (all except Sheet, Nr, Name, Location)
                            file_cols = [col for col in filtered_df.columns if col not in ["Sheet", "Nr", "Name", "Location"]]

                            # Build column config dynamically
                            col_config = {
                                "Sheet": st.column_config.TextColumn(width="small"),
                                "Nr": st.column_config.TextColumn(width="small"),
                                "Name": st.column_config.TextColumn(width="medium"),
                                "Location": st.column_config.TextColumn(width="small"),
                            }

                            for file_col in file_cols:
                                col_config[file_col] = st.column_config.TextColumn(width="small")

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
                                file_name="xls_differences.csv",
                                mime="text/csv",
                                key="xls_download"
                            )

                        else:
                            st.info("No differences found! All files are identical.")

                except Exception as e:
                    st.error(f"Error during XLS comparison: {str(e)}")
    else:
        st.info("👈 Upload at least 2 XLS files to compare")

# CSV COMPARISON TAB
with tab2:
    if csv_files and len(csv_files) >= 2:
        if st.button("Run CSV Comparison", key="csv_run", type="primary", use_container_width=True):
            with st.spinner("Loading and comparing CSV files..."):
                try:
                    files_data = {}
                    with tempfile.TemporaryDirectory() as tmpdir:
                        for uploaded_file in csv_files:
                            temp_path = Path(tmpdir) / uploaded_file.name
                            with open(temp_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())

                            file_label = Path(uploaded_file.name).stem
                            files_data[file_label] = parse_csv_file(str(temp_path))

                        diffs = compare_csv_files(files_data)

                        if diffs:
                            df = pd.DataFrame(diffs)

                            st.success(f"✓ Found **{len(df)}** difference locations across **{len(csv_files)}** files")

                            # Filter by group
                            groups = df["Group"].unique().tolist()
                            group_filter = st.multiselect(
                                "Filter by Group",
                                groups,
                                default=groups,
                                key="csv_group_filter"
                            )

                            filtered_df = df[df["Group"].isin(group_filter)].copy()

                            st.subheader(f"Differences ({len(filtered_df)} locations)")

                            # Get file columns (all except Group, Sub-group, Name, Dimension)
                            file_cols = [col for col in filtered_df.columns if col not in ["Group", "Sub-group", "Name", "Dimension"]]

                            # Build column config
                            col_config = {
                                "Group": st.column_config.TextColumn(width="small"),
                                "Sub-group": st.column_config.TextColumn(width="small"),
                                "Name": st.column_config.TextColumn(width="medium"),
                                "Dimension": st.column_config.TextColumn(width="small"),
                            }

                            for file_col in file_cols:
                                col_config[file_col] = st.column_config.TextColumn(width="small")

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
                                file_name="csv_differences.csv",
                                mime="text/csv",
                                key="csv_download"
                            )

                        else:
                            st.info("No differences found! All files are identical.")

                except Exception as e:
                    st.error(f"Error during CSV comparison: {str(e)}")
    else:
        st.info("👈 Upload at least 2 CSV files to compare")
