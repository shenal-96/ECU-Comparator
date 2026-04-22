"""Compare multiple XLS files and find differences."""

from itertools import combinations
from typing import Dict, List, Any


def compare_all_pairs(files: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Compare all pairs of files. files = {label: parsed_data}

    Returns flat list of diff rows.
    """
    diffs = []

    file_list = list(files.items())
    for label_a, data_a in file_list:
        for label_b, data_b in file_list:
            if label_a >= label_b:
                continue

            diffs.extend(compare_pair(label_a, data_a, label_b, data_b))

    return sorted(diffs, key=lambda x: (x["File A"], x["File B"], x["Sheet"], x["Nr"]))


def compare_pair(
    label_a: str, data_a: Dict, label_b: str, data_b: Dict
) -> List[Dict[str, Any]]:
    """Compare one pair of files."""
    diffs = []

    sheets_a = data_a.get("sheets", {})
    sheets_b = data_b.get("sheets", {})

    diffs.extend(
        compare_parameter(label_a, sheets_a.get("Parameter", {}),
                         label_b, sheets_b.get("Parameter", {}))
    )
    diffs.extend(
        compare_val_2d(label_a, sheets_a.get("Val_2D", {}),
                      label_b, sheets_b.get("Val_2D", {}))
    )
    diffs.extend(
        compare_val_3d(label_a, sheets_a.get("Val_3D", {}),
                      label_b, sheets_b.get("Val_3D", {}))
    )

    return diffs


def compare_parameter(label_a: str, param_a: Dict, label_b: str, param_b: Dict) -> List[Dict]:
    """Compare Parameter sheets."""
    diffs = []

    shared_nrs = set(param_a.keys()) & set(param_b.keys())

    for nr in shared_nrs:
        val_a = param_a[nr].get("value")
        val_b = param_b[nr].get("value")

        if val_a is None or val_b is None:
            continue

        if abs(val_a - val_b) > 1e-9:
            diffs.append({
                "File A": label_a,
                "File B": label_b,
                "Sheet": "Parameter",
                "Nr": nr,
                "Name": param_a[nr].get("name", ""),
                "Location": "Value",
                "Value A": round(val_a, 6) if val_a else 0,
                "Value B": round(val_b, 6) if val_b else 0,
                "Delta": round(val_b - val_a, 6),
            })

    return diffs


def compare_val_2d(label_a: str, val_2d_a: Dict, label_b: str, val_2d_b: Dict) -> List[Dict]:
    """Compare Val_2D sheets."""
    diffs = []

    shared_nrs = set(val_2d_a.keys()) & set(val_2d_b.keys())

    for nr in shared_nrs:
        y_vals_a = val_2d_a[nr].get("y_values", [])
        y_vals_b = val_2d_b[nr].get("y_values", [])

        for idx in range(max(len(y_vals_a), len(y_vals_b))):
            val_a = y_vals_a[idx] if idx < len(y_vals_a) else None
            val_b = y_vals_b[idx] if idx < len(y_vals_b) else None

            if val_a is None or val_b is None:
                continue

            if abs(val_a - val_b) > 1e-9:
                diffs.append({
                    "File A": label_a,
                    "File B": label_b,
                    "Sheet": "Val_2D",
                    "Nr": nr,
                    "Name": val_2d_a[nr].get("name", ""),
                    "Location": f"y[{idx}]",
                    "Value A": round(val_a, 6),
                    "Value B": round(val_b, 6),
                    "Delta": round(val_b - val_a, 6),
                })

    return diffs


def compare_val_3d(label_a: str, val_3d_a: Dict, label_b: str, val_3d_b: Dict) -> List[Dict]:
    """Compare Val_3D sheets."""
    diffs = []

    shared_nrs = set(val_3d_a.keys()) & set(val_3d_b.keys())

    for nr in shared_nrs:
        grid_a = val_3d_a[nr].get("grid", [])
        grid_b = val_3d_b[nr].get("grid", [])

        for row_idx in range(max(len(grid_a), len(grid_b))):
            row_a = grid_a[row_idx] if row_idx < len(grid_a) else []
            row_b = grid_b[row_idx] if row_idx < len(grid_b) else []

            for col_idx in range(max(len(row_a), len(row_b))):
                val_a = row_a[col_idx] if col_idx < len(row_a) else None
                val_b = row_b[col_idx] if col_idx < len(row_b) else None

                if val_a is None or val_b is None:
                    continue

                if abs(val_a - val_b) > 1e-9:
                    diffs.append({
                        "File A": label_a,
                        "File B": label_b,
                        "Sheet": "Val_3D",
                        "Nr": nr,
                        "Name": val_3d_a[nr].get("name", ""),
                        "Location": f"[{row_idx}][{col_idx}]",
                        "Value A": round(val_a, 6),
                        "Value B": round(val_b, 6),
                        "Delta": round(val_b - val_a, 6),
                    })

    return diffs
