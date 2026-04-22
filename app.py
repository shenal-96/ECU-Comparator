"""Streamlit app for comparing ECU parameter files."""

import streamlit as st
import pandas as pd
import tempfile
from pathlib import Path
from parser import parse_file
from multi_file_comparator import compare_all_files


st.set_page_config(page_title="ECU Comparator", layout="wide")
st.title("ECU Parameter File Comparator")

with st.sidebar:
    st.header("Upload Files")

    uploaded_files = st.file_uploader(
        "Select .XLS files to compare",
        type=["xls", "xlsx"],
        accept_multiple_files=True,
        help="Upload 2 or more ECU parameter .XLS files"
    )

    if uploaded_files:
        st.info(f"✓ {len(uploaded_files)} file(s) uploaded")
        run_button = st.button("Run Comparison", key="run", type="primary", use_container_width=True)
    else:
        st.warning("Please upload at least 2 .XLS files to compare")
        run_button = False

st.divider()

if run_button and uploaded_files and len(uploaded_files) >= 2:
    with st.spinner("Loading and comparing files..."):
        try:
            files_data = {}
            with tempfile.TemporaryDirectory() as tmpdir:
                for uploaded_file in uploaded_files:
                    temp_path = Path(tmpdir) / uploaded_file.name
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    file_label = Path(uploaded_file.name).stem
                    files_data[file_label] = parse_file(str(temp_path))

                diffs = compare_all_files(files_data)

                if diffs:
                    df = pd.DataFrame(diffs)

                    st.success(f"✓ Found **{len(diffs)}** difference locations across **{len(uploaded_files)}** files")

                    # Filter by sheet
                    sheet_filter = st.multiselect(
                        "Filter by Sheet",
                        ["Parameter", "Val_2D", "Val_3D"],
                        default=["Parameter", "Val_2D", "Val_3D"],
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
                        col_config[file_col] = st.column_config.NumberColumn(width="small", format="%.6g")

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
