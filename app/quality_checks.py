from __future__ import annotations
import pandas as pd

def quality_warnings(sheet_name: str, df: pd.DataFrame, col_profile: pd.DataFrame) -> pd.DataFrame:
    warnings = []

    for _, r in col_profile.iterrows():
        miss = r["bos_oran"]
        col = r["kolon_adi"]
        dtype_label = r["tahmini_tip"]
        uniq_ratio = r["unique_oran"]

        if miss >= 99.0:
            warnings.append((sheet_name, "ERROR", "Tamamen boş kolon", col, f"%{miss} boş", miss))
        elif miss >= 95.0:
            warnings.append((sheet_name, "WARN", "Neredeyse boş kolon", col, f"%{miss} boş", miss))

        if dtype_label == "text" and uniq_ratio >= 90.0 and len(df) > 50:
            warnings.append((sheet_name, "INFO", "Çok yüksek unique oranı", col, f"%{uniq_ratio} unique (free-text olabilir)", uniq_ratio))

    return pd.DataFrame(warnings, columns=["sheet_adi","seviye","konu","kolon_adi","detay","etkilenen_oran"])

def duplicate_analysis(sheet_name: str, df: pd.DataFrame) -> pd.DataFrame:
    n = len(df)
    dup_count = int(df.duplicated().sum()) if n else 0
    dup_ratio = (dup_count / n * 100) if n else 0.0
    return pd.DataFrame([{
        "sheet_adi": sheet_name,
        "tam_satir_duplicate_sayisi": dup_count,
        "tam_satir_duplicate_oran": round(dup_ratio, 2),
    }])
