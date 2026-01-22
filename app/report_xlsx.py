from __future__ import annotations
import pandas as pd

def write_report_xlsx(out_path: str,
                      genel_ozet: pd.DataFrame,
                      sheet_list: pd.DataFrame,
                      col_profile: pd.DataFrame,
                      warnings_df: pd.DataFrame,
                      dup_df: pd.DataFrame) -> None:
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        genel_ozet.to_excel(writer, index=False, sheet_name="00_Genel_Ozet")
        sheet_list.to_excel(writer, index=False, sheet_name="01_Sheet_Listesi")
        col_profile.to_excel(writer, index=False, sheet_name="02_Kolon_Profili")
        warnings_df.to_excel(writer, index=False, sheet_name="03_Verı_Kalıte_Uyarıları")
        dup_df.to_excel(writer, index=False, sheet_name="04_Duplicate_Analizi")
