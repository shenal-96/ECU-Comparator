"""Streamlit app for comparing ECU parameter files (XLS/XLSX/CSV)."""

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

# Separate file uploaders for XLS, XLSX, and CSV
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("XLS Files")
    xls_files = st.file_uploader(
        "Select .XLS files",
        type=["xls"],
        accept_multiple_files=True,
        key="xls_uploader",
        help="Upload ECU parameter .XLS files (old format)"
    )

with col2:
    st.subheader("XLSX Files")
    xlsx_files = st.file_uploader(
        "Select .XLSX files",
        type=["xlsx"],
        accept_multiple_files=True,
        key="xlsx_uploader",
        help="Upload ECU parameter .XLSX files (modern format)"
    )

with col3:
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
tab1, tab2, tab3 = st.tabs(["XLS Comparison", "XLSX Comparison", "CSV Comparison"])

# Helper function for XLS/XLSX comparison
def compare_xls_or_xlsx_files(files_list, tab_name, download_name):
    if files_list and len(files_list) >= 2:
        if st.button(f"Run {tab_name} Comparison", key=f"{tab_name.lower()}_run", type="primary", use_container_width=True):
            with st.spinner(f"Loading and comparing {tab_name} files..."):
                try:
                    files_data = {}
                    with tempfile.TemporaryDirectory() as tmpdir:
                        for uploaded_file in files_list:
                            temp_path = Path(tmpdir) / uploaded_file.name
                            with open(temp_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())

                            file_label = Path(uploaded_file.name).stem
                            files_data[file_label] = parse_file(str(temp_path))

                        diffs = compare_all_files(files_data)

                        if diffs:
                            df = pd.DataFrame(diffs)

                            st.success(f"✓ Found **{len(df)}** difference locations across **{len(files_list)}** files")

                            # Filter by sheet
                            sheet_filter = st.multiselect(
                                "Filter by Sheet",
                                ["Parameter", "Val_2D", "Val_3D"],
                                default=["Parameter", "Val_2D", "Val_3D"],
                                key=f"{tab_name.lower()}_sheet_filter"
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
                                file_name=f"{download_name}_differences.csv",
                                mime="text/csv",
                                key=f"{tab_name.lower()}_download"
                            )

                        else:
                            st.info("No differences found! All files are identical.")

                except Exception as e:
                    st.error(f"Error during {tab_name} comparison: {str(e)}")
    else:
        st.info(f"👈 Upload at least 2 {tab_name} files to compare")


# XLS COMPARISON TAB
with tab1:
    compare_xls_or_xlsx_files(xls_files, "XLS", "xls")

# XLSX COMPARISON TAB
with tab2:
    compare_xls_or_xlsx_files(xlsx_files, "XLSX", "xlsx")

# CSV COMPARISON TAB
with tab3:
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
