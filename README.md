# ECU Parameter File Comparator

A web tool for comparing multiple ECU parameter .XLS files side-by-side and identifying differences.

## Features

- **Upload multiple .XLS files** — Compare 2 or more ECU calibration files at once
- **All-pairs comparison** — Every file is compared against every other file
- **Multi-sheet analysis** — Compares Parameter, Val_2D (1D curves), and Val_3D (2D maps) sheets
- **Cell-level detail** — Shows exact location and value differences with delta calculation
- **Filterable results** — Filter by sheet type and file pair
- **CSV export** — Download comparison results as CSV

## Live Demo

🚀 **[Open in Streamlit Cloud](https://ecu-comparator.streamlit.app)**

## Local Development

### Prerequisites

- Python 3.9+
- pip

### Installation

```bash
git clone https://github.com/shenalperera/ECU-Comparator.git
cd ECU-Comparator
pip install -r requirements.txt
```

### Run Locally

```bash
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

## How to Use

1. **Upload files** — Click the file uploader in the sidebar and select 2 or more .XLS files
2. **Run comparison** — Click "Run Comparison" button
3. **View results** — See all differences in the table below
4. **Filter** — Use the sheet and file pair filters to focus on specific comparisons
5. **Export** — Click "Download as CSV" to save results

## File Format

The tool expects ECU parameter .XLS files with the following sheets:

- **General** — Metadata (CRC, engine number, date, operator)
- **Parameter** — Scalar tuning parameters (1846 rows typical)
- **Desc_2D** — 1D curve metadata
- **Val_2D** — 1D curve values
- **Desc_3D** — 2D map metadata
- **Val_3D** — 2D map values

## Project Structure

```
ECU-Comparator/
├── app.py           # Streamlit UI
├── parser.py        # XLS file reader
├── comparator.py    # All-pairs diff logic
├── requirements.txt # Dependencies
└── README.md        # This file
```

## Technical Details

### Parser (`parser.py`)

Reads .XLS files using `xlrd` and extracts structured data:
- Parameter sheet → dict keyed by Nr (parameter ID)
- Val_2D sheet → dict with curve metadata and y-axis values
- Val_3D sheet → dict with grid data, x/y axes

### Comparator (`comparator.py`)

All-pairs comparison logic:
- Iterates all file combinations
- Cell-by-cell diff detection
- Returns flat list of differences with File A, File B, Sheet, Nr, Name, Location, Value A/B, Delta

### App (`app.py`)

Streamlit web interface:
- File upload via sidebar
- Configurable filters (sheet type, file pair)
- Interactive data table
- CSV download

## Dependencies

- **streamlit** — Web framework
- **xlrd** — Read .XLS files (v1.2.0 required for old format)
- **pandas** — Data manipulation
- **openpyxl** — Excel support

## License

MIT

## Author

Created for ECU parameter calibration analysis
