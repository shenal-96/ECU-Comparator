"""Streamlit app for comparing ECU parameter files."""

import streamlit as st
import pandas as pd
from pathlib import Path
from parser import parse_file
from comparator import compare_all_pairs


st.set_page_config(page_title="ECU Comparator", layout="wide")
st.title("ECU Parameter File Comparator")

DEFAULT_PATH = "/Users/shenalperera/Downloads/ECU - Parameter files"

with st.sidebar:
    st.header("Configuration")

    folder_path = st.text_input(
        "Folder path",
        value=DEFAULT_PATH,
        help="Path to folder containing .XLS files"
    )

    if Path(folder_path).exists():
        files = sorted(Path(folder_path).glob("*.XLS"))
        file_names = [f.name for f in files]

        selected_files = st.multiselect(
            "Select files to compare",
            file_names,
            default=file_names[:3] if len(file_names) >= 3 else file_names,
        )

        selected_paths = [Path(folder_path) / f for f in selected_files]

        run_button = st.button("Run Comparison", key="run", type="primary", use_container_width=True)
    else:
        st.error(f"Folder not found: {folder_path}")
        run_button = False

st.divider()

if run_button and selected_paths:
    with st.spinner("Loading and comparing files..."):
        try:
            files_data = {}
            for fpath in selected_paths:
                files_data[fpath.stem] = parse_file(str(fpath))

            diffs = compare_all_pairs(files_data)

            if diffs:
                df = pd.DataFrame(diffs)

                st.success(f"✓ Found **{len(diffs)}** differences across **{len(selected_files)}** files")

                col1, col2 = st.columns(2)
                with col1:
                    sheet_filter = st.multiselect(
                        "Filter by Sheet",
                        ["Parameter", "Val_2D", "Val_3D"],
                        default=["Parameter", "Val_2D", "Val_3D"],
                    )

                with col2:
                    file_pairs = df.apply(lambda x: f"{x['File A']} ↔ {x['File B']}", axis=1).unique()
                    pair_filter = st.multiselect(
                        "Filter by File Pair",
                        file_pairs,
                        default=list(file_pairs)[:5],
                    )

                filtered_df = df[
                    (df["Sheet"].isin(sheet_filter)) &
                    (df.apply(lambda x: f"{x['File A']} ↔ {x['File B']}", axis=1).isin(pair_filter))
                ]

                st.subheader(f"Differences ({len(filtered_df)} rows)")
                st.dataframe(
                    filtered_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "File A": st.column_config.TextColumn(width="small"),
                        "File B": st.column_config.TextColumn(width="small"),
                        "Sheet": st.column_config.TextColumn(width="small"),
                        "Nr": st.column_config.TextColumn(width="small"),
                        "Name": st.column_config.TextColumn(width="medium"),
                        "Location": st.column_config.TextColumn(width="small"),
                        "Value A": st.column_config.NumberColumn(width="small", format="%.6f"),
                        "Value B": st.column_config.NumberColumn(width="small", format="%.6f"),
                        "Delta": st.column_config.NumberColumn(width="small", format="%.6f"),
                    }
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
