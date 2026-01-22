from __future__ import annotations
import pandas as pd

def guess_dtype(series: pd.Series) -> str:
    if pd.api.types.is_bool_dtype(series):
        return "bool"
    if pd.api.types.is_integer_dtype(series):
        return "int"
    if pd.api.types.is_float_dtype(series):
        return "float"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "date"
    return "text"

def profile_columns(sheet_name: str, df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    n = len(df)

    for col in df.columns:
        s = df[col]
        missing = int(s.isna().sum())
        filled = int(n - missing)
        miss_ratio = (missing / n) if n > 0 else 0.0

        non_na = s.dropna()
        unique = int(non_na.nunique()) if len(non_na) else 0
        uniq_ratio = (unique / filled) if filled > 0 else 0.0

        dtype_label = guess_dtype(s)

        min_v = max_v = mean_v = median_v = None
        top1 = top2 = top3 = None

        if dtype_label in ("int", "float"):
            nums = pd.to_numeric(non_na, errors="coerce").dropna()
            if len(nums):
                min_v = float(nums.min())
                max_v = float(nums.max())
                mean_v = float(nums.mean())
                median_v = float(nums.median())
        elif dtype_label == "date":
            dates = pd.to_datetime(non_na, errors="coerce").dropna()
            if len(dates):
                min_v = str(dates.min().date())
                max_v = str(dates.max().date())
        else:
            vc = non_na.astype(str).value_counts(dropna=True)
            if len(vc):
                top1 = vc.index[0]
                top2 = vc.index[1] if len(vc) > 1 else None
                top3 = vc.index[2] if len(vc) > 2 else None

        examples = ", ".join([str(x) for x in non_na.head(3).tolist()])

        rows.append({
            "sheet_adi": sheet_name,
            "kolon_adi": str(col),
            "tahmini_tip": dtype_label,
            "dolu_sayi": filled,
            "bos_sayi": missing,
            "bos_oran": round(miss_ratio * 100, 2),
            "unique_sayi": unique,
            "unique_oran": round(uniq_ratio * 100, 2),
            "min": min_v,
            "max": max_v,
            "ortalama": mean_v,
            "median": median_v,
            "en_sik_1": top1,
            "en_sik_2": top2,
            "en_sik_3": top3,
            "ornek_degerler": examples
        })

    return pd.DataFrame(rows)
