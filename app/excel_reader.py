from __future__ import annotations
import pandas as pd

def read_excel_all_sheets(path: str) -> dict:
    xls = pd.ExcelFile(path)
    result = {}

    for sheet_name in xls.sheet_names:
        # Basit V1: direkt header=0 okuyalım (karışık header tahmini v1.1'e bırakıyoruz)
        df = pd.read_excel(path, sheet_name=sheet_name, header=0)
        df = df.dropna(how="all")
        result[sheet_name] = {"df": df, "header_row": 1}

    return result
