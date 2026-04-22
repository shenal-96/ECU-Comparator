"""Parse ECU parameter .XLS files into structured dicts."""

import xlrd
from pathlib import Path
from typing import Dict, Any, List, Tuple


def parse_file(filepath: str) -> Dict[str, Any]:
    """Load and parse a single XLS file.

    Returns dict with 'label' and 'sheets' (containing Parameter, Val_2D, Val_3D).
    """
    wb = xlrd.open_workbook(filepath)

    label = Path(filepath).stem
    sheets = {}

    for sheet in wb.sheets():
        if sheet.name == "Parameter":
            sheets["Parameter"] = parse_parameter(sheet)
        elif sheet.name == "Val_2D":
            sheets["Val_2D"] = parse_val_2d(sheet)
        elif sheet.name == "Val_3D":
            sheets["Val_3D"] = parse_val_3d(sheet)

    return {"label": label, "sheets": sheets}


def parse_parameter(sheet) -> Dict[str, Dict[str, Any]]:
    """Parse Parameter sheet: Nr -> {name, value, unit}."""
    result = {}

    for row_idx in range(1, sheet.nrows):
        try:
            nr = sheet.cell_value(row_idx, 0)
            if not nr:
                continue

            name = sheet.cell_value(row_idx, 1)
            value = sheet.cell_value(row_idx, 2)
            unit = sheet.cell_value(row_idx, 3)

            try:
                value = float(value) if value else None
            except (ValueError, TypeError):
                value = None

            result[str(int(nr) if isinstance(nr, float) else nr)] = {
                "name": str(name) if name else "",
                "value": value,
                "unit": str(unit) if unit else "",
            }
        except Exception:
            continue

    return result


def parse_val_2d(sheet) -> Dict[str, Dict[str, Any]]:
    """Parse Val_2D sheet. Each curve = 4 rows: [id, x-axis, y-axis, blank].

    Returns: Nr -> {name, x_values, y_values}
    """
    result = {}
    row_idx = 1

    while row_idx < sheet.nrows:
        try:
            nr = sheet.cell_value(row_idx, 0)
            if not nr:
                row_idx += 1
                continue

            name = sheet.cell_value(row_idx, 1)
            nr_key = str(int(nr) if isinstance(nr, float) else nr)

            if row_idx + 2 >= sheet.nrows:
                row_idx += 4
                continue

            x_row = row_idx + 1
            y_row = row_idx + 2

            x_values = []
            y_values = []

            for col in range(2, sheet.ncols):
                x_val = sheet.cell_value(x_row, col)
                y_val = sheet.cell_value(y_row, col)

                try:
                    x_values.append(float(x_val) if x_val else 0)
                    y_values.append(float(y_val) if y_val else 0)
                except (ValueError, TypeError):
                    pass

            result[nr_key] = {
                "name": str(name) if name else "",
                "x_values": x_values,
                "y_values": y_values,
            }

            row_idx += 4
        except Exception:
            row_idx += 4

    return result


def parse_val_3d(sheet) -> Dict[str, Dict[str, Any]]:
    """Parse Val_3D sheet. Structure: identifier row has Nr, Name, then x-axis starting at col E.
    Data rows: col D has y-axis, cols E+ have grid values.
    """
    result = {}
    row_idx = 1

    while row_idx < sheet.nrows:
        try:
            nr = sheet.cell_value(row_idx, 0)
            if not nr or nr == "":
                row_idx += 1
                continue

            # Skip rows without a numeric Nr (floating point number)
            if not isinstance(nr, float):
                row_idx += 1
                continue

            name = sheet.cell_value(row_idx, 1)
            nr_key = str(int(nr))

            # First pass: get x-axis values from identifier row (col F onward, index 5+)
            x_values = []
            for col in range(5, sheet.ncols):
                x_val = sheet.cell_value(row_idx, col)
                # Stop on empty string (not when value is 0)
                if x_val == "":
                    break
                try:
                    x_values.append(float(x_val))
                except (ValueError, TypeError):
                    break

            y_values = []
            grid = []
            data_row = row_idx + 1

            # Parse data rows until we hit a separator
            while data_row < sheet.nrows:
                # Column E (index 4) contains y-axis breakpoints in data rows
                y_val = sheet.cell_value(data_row, 4)
                col_c = sheet.cell_value(data_row, 2)

                # Empty row = separator between maps
                if (not y_val or y_val == "") and (not col_c or col_c == ""):
                    break

                # Skip "rpm" header row (col C = "rpm", index 2)
                if isinstance(col_c, str) and col_c.lower() == "rpm":
                    data_row += 1
                    continue

                # Parse y-axis value (must be numeric)
                try:
                    y_num = float(y_val) if y_val else None
                except (ValueError, TypeError):
                    data_row += 1
                    continue

                if y_num is None:
                    data_row += 1
                    continue

                y_values.append(y_num)

                # Grid values start at column F (index 5) matching x-axis column positions
                row_values = []
                for col in range(5, 5 + len(x_values)):
                    if col >= sheet.ncols:
                        break
                    cell_val = sheet.cell_value(data_row, col)
                    try:
                        row_values.append(float(cell_val) if cell_val != "" else 0)
                    except (ValueError, TypeError):
                        row_values.append(0)

                if row_values:
                    grid.append(row_values)

                data_row += 1

            result[nr_key] = {
                "name": str(name) if name else "",
                "x_values": x_values,
                "y_values": y_values,
                "grid": grid,
            }

            row_idx = data_row + 1
        except Exception:
            row_idx += 1

    return result
