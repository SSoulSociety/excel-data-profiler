from __future__ import annotations
import pandas as pd

from .header_detector import detect_header_row


def read_excel_all_sheets(path: str, auto_header: bool = True, preview_rows: int = 30) -> dict:
    xls = pd.ExcelFile(path)
    result = {}

    for sheet_name in xls.sheet_names:
        header_row_0 = 0
        confidence = 0.0

        if auto_header:
            # preview read (no header)
            preview_df = pd.read_excel(path, sheet_name=sheet_name, header=None, nrows=preview_rows)
            header_row_0, confidence = detect_header_row(preview_df, max_rows=preview_rows)

        # full read using detected header
        df = pd.read_excel(path, sheet_name=sheet_name, header=header_row_0)
        df = df.dropna(how="all")

        result[sheet_name] = {
            "df": df,
            "header_row": int(header_row_0 + 1),  # 1-based for humans
            "header_confidence": float(confidence),
        }

    return result
