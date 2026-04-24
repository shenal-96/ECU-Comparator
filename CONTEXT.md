# ECU Comparator - Project Context

**Project**: ECU Parameter File Comparator  
**Created**: April 22-24, 2026  
**Status**: Production Ready (Streamlit Cloud Deployed)  
**Purpose**: Compare multiple ECU parameter configuration files (.XLS, .XLSX, .CSV) to identify differences across all files

---

## Overview

A web-based comparison tool built with Streamlit that allows engineers to upload multiple configuration files and see exactly where differences exist across all files in a single unified view.

**Key Feature**: Compare up to 8 files at once, see all values at each difference location in one row, no "File A vs File B" pairwise approach.

---

## Architecture

### Three Independent Comparison Workflows

The app provides three completely separate tabs for different file formats:

1. **XLS Comparison** — Old Excel format ECU parameter files
   - Sheets: Parameter, Val_2D (1D curves), Val_3D (2D maps)
   - Comparison shows all file values at each difference location
   - Filters by sheet type

2. **XLSX Comparison** — Modern Excel format ECU parameter files
   - Same sheet structure as XLS
   - Identical comparison logic
   - Separate upload and results from XLS

3. **CSV Comparison** — ComAp controller configuration files
   - Semicolon-delimited format with hierarchical structure
   - Columns: Group, Sub-group, Name, Value, Dimension
   - Filters by Group
   - Completely separate dataset from XLS/XLSX

---

## File Structure

```
ECU-Comparator/
├── app.py                    # Main Streamlit UI (3 tabs, independent workflows)
├── parser.py                 # XLS/XLSX file parser (uses pandas)
├── csv_parser.py             # CSV file parser (ComAp format)
├── multi_file_comparator.py  # XLS/XLSX all-files comparison logic
├── csv_comparator.py         # CSV all-files comparison logic
├── requirements.txt          # Python dependencies
├── packages.txt              # System-level packages for Streamlit Cloud
├── .streamlit/
│   └── config.toml           # Streamlit configuration
├── README.md                 # User documentation
└── CONTEXT.md                # This file
```

---

## Core Components

### 1. Parser Module (`parser.py`)

**Function**: `parse_file(filepath: str) -> Dict[str, Any]`

Reads XLS/XLSX files using pandas (auto-detects format) and extracts three sheets:

- **Parameter**: Scalar tuning parameters
  - Key: Nr (numeric ID like 10010002)
  - Data: name, value, unit
  - ~1846 entries per file

- **Val_2D**: 1D lookup curves
  - Key: Nr
  - Data: x_values (axis), y_values (output curve)
  - ~87 curves per file

- **Val_3D**: 2D lookup maps
  - Key: Nr
  - Data: x_values, y_values, grid (2D array of values)
  - ~62 maps per file

**Technical Details**:
- Uses pandas `read_excel()` which auto-detects .xls vs .xlsx
- Handles asymmetric column structures in Val_3D
- Skips empty rows and header markers
- Returns label (filename stem) and structured data dict

### 2. CSV Parser Module (`csv_parser.py`)

**Function**: `parse_csv_file(filepath: str) -> Dict[str, Any]`

Reads ComAp semicolon-delimited CSV files:

- **Format**: Hierarchical with rows 1-2 (header), rows 4+ (data)
- **Key columns**: Group, Sub-group, Name, Value, Dimension
- **Key structure**: Composite key `{Group}|{Sub-group}|{Name}`
- **Data**: Stores string value, attempts numeric conversion, tracks dimension unit

**Technical Details**:
- Skips first 4 rows (metadata)
- Handles missing/empty cells gracefully
- Attempts float conversion for numeric values
- Returns type="csv" flag to distinguish from XLS files

### 3. Multi-File Comparator (`multi_file_comparator.py`)

**Function**: `compare_all_files(files: Dict[str, Dict]) -> List[Dict]`

Compares XLS/XLSX files across all sheets simultaneously:

- **Input**: Dictionary of {file_label: parsed_data}
- **Output**: List of difference rows, each showing all file values at that location
- **Logic**:
  - For each unique Nr/Location, collect all file values
  - Flag if any file differs from others
  - Return location with all file values in separate columns

**Three internal functions**:
- `compare_parameter_all()` — Scalar parameter comparison
- `compare_val_2d_all()` — 1D curve comparison (by y-value index)
- `compare_val_3d_all()` — 2D map comparison (by grid cell)

**Floating-point handling**: Uses `round(val, 9)` to avoid precision artifacts

### 4. CSV Comparator (`csv_comparator.py`)

**Function**: `compare_csv_files(files: Dict[str, Dict]) -> List[Dict]`

Compares CSV files across all parameters:

- **Input**: Dictionary of {file_label: parsed_data with type="csv"}
- **Output**: List of difference rows with Group, Sub-group, Name, Dimension columns + all file values
- **Logic**:
  - Iterate shared keys (composite hierarchical keys)
  - Compare both string and numeric values
  - Flag if any unique values exist across files

---

## Streamlit App (`app.py`)

### Layout

**Header**:
- Title: "ECU Parameter File Comparator"
- Three columns for file uploaders (XLS | XLSX | CSV)

**Tabs**:
1. XLS Comparison
2. XLSX Comparison
3. CSV Comparison

### Workflow (XLS/XLSX)

1. Upload 2+ files via sidebar
2. Click "Run XLS/XLSX Comparison"
3. App temp-saves files, parses, compares
4. Display results:
   - Success banner showing diff count
   - Sheet filter multiselect
   - Data table with columns: Sheet | Nr | Name | Location | [File1] | [File2] | ...
   - CSV download button

### Workflow (CSV)

1. Upload 2+ CSV files via sidebar
2. Click "Run CSV Comparison"
3. App temp-saves files, parses, compares
4. Display results:
   - Success banner showing diff count
   - Group filter multiselect
   - Data table with columns: Group | Sub-group | Name | Dimension | [File1] | [File2] | ...
   - CSV download button

### Key Features

- **Dynamic column configuration**: File columns displayed as TextColumns (supports both string and numeric)
- **Temp file handling**: Uses `tempfile.TemporaryDirectory()` for secure file handling on cloud
- **Error handling**: Try/except wraps full comparison with user-friendly error messages
- **Independent workflows**: Each tab is completely isolated (separate buttons, filters, downloads)

---

## Dependencies

```
streamlit>=1.28.0      # Web UI framework
pandas>=2.0.0          # Excel/CSV reading, data manipulation
openpyxl>=3.1.0        # Excel backend for pandas
```

**Why no xlrd?** Switched from xlrd (build issues on Streamlit Cloud) to pandas, which auto-detects both .xls and .xlsx formats.

---

## Data Flow

### XLS/XLSX Files

```
[User uploads .xls/.xlsx]
    ↓
[parse_file() via pandas]
    ├→ Parameter sheet → {Nr: {name, value, unit}}
    ├→ Val_2D sheet → {Nr: {name, x_values, y_values}}
    └→ Val_3D sheet → {Nr: {name, x_values, y_values, grid}}
    ↓
[compare_all_files()]
    ├→ compare_parameter_all()
    ├→ compare_val_2d_all()
    └→ compare_val_3d_all()
    ↓
[Display table with all file values per location]
    ↓
[Download as CSV]
```

### CSV Files

```
[User uploads .csv]
    ↓
[parse_csv_file() via pandas]
    └→ {Group|Sub-group|Name: {group, sub_group, name, value, numeric_value, dimension}}
    ↓
[compare_csv_files()]
    └→ Compare all keys, flag differences
    ↓
[Display table with all file values per location]
    ↓
[Download as CSV]
```

---

## Deployment

### Streamlit Cloud

**Repository**: `shenal-96/ECU-Comparator`  
**Branch**: `main`  
**URL**: https://ecu-comparator.streamlit.app

**Deployment Steps**:
1. Files committed to GitHub
2. Visit https://share.streamlit.io
3. Select repository and main file (app.py)
4. Deploy button

**Special Files**:
- `.streamlit/config.toml` — Theme and server config
- `packages.txt` — System dependencies (build-essential for xlrd fallback)
- `.gitignore` — Cache, secrets, __pycache__

---

## Integration with PQA Project

### Intended Merge

The ECU Comparator module can be merged into the PQA project as a feature that:

1. **Adds CSV comparison capability** to PQA dashboard
   - Reuse `csv_parser.py` and `csv_comparator.py`
   - Add "CSV Comparison" tab to main PQA app

2. **Adds XLS/XLSX comparison capability**
   - Reuse `parser.py` and `multi_file_comparator.py`
   - Could integrate as alternative comparison mode in PQA

### Files to Migrate

**Core logic** (language/framework agnostic):
- `csv_parser.py`
- `csv_comparator.py`
- `parser.py`
- `multi_file_comparator.py`

**Integration point**:
- Extract UI code from `app.py` into PQA's existing Streamlit structure
- Reuse comparison functions, adapt to PQA's sidebar/session state pattern

**No breaking changes** — these modules work independently and can be imported into PQA without modification.

---

## Known Limitations

1. **File size**: Streamlit Cloud max upload ~200MB (configurable in `.streamlit/config.toml`)
2. **Memory**: Large files (100+ MB) may timeout on free tier
3. **Floating-point precision**: Uses 9-decimal rounding for numeric comparison
4. **CSV format**: Hard-coded for ComAp semicolon-delimited format (would need adaptation for other CSV schemas)
5. **XLS/XLSX sheets**: Expects specific sheet names (Parameter, Val_2D, Val_3D) — won't parse other structures

---

## Future Enhancements

1. **Batch processing**: Allow file uploads in bulk zip archives
2. **Difference export formats**: Support Excel, JSON, HTML reports
3. **Change tracking**: Show which files changed vs which stayed the same
4. **Diff visualization**: Highlight changed cells with colors
5. **CSV schema flexibility**: Support custom CSV column mappings
6. **API endpoint**: Expose comparison logic as REST API for external tools

---

## Testing Notes

- Tested with 7 ECU .XLS files (all identical schema, 1846 Parameters, 87 Val_2D, 62 Val_3D)
- Verified 21 file pairs all-pairs comparison (~1000 total diffs)
- Verified Parameter, Val_2D, Val_3D filtering works
- CSV tested with ComAp BE.csv (semicolon-delimited, ~700 parameters)
- Streamlit Cloud deployment successful (resolved xlrd → pandas migration)

---

## Author Notes

Built as web-based replacement for manual Excel diff workflows. Key design decision: **show all file values in one row per location** rather than pairwise comparisons, allowing engineers to spot patterns across 8+ files instantly.

Uses Streamlit for simplicity, pandas for robust file handling, minimal dependencies for cloud reliability.
