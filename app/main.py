from __future__ import annotations
import os
import pandas as pd

from .ui import pick_excel_file
from .utils import ensure_dir, now_stamp
from .excel_reader import read_excel_all_sheets
from .sampler import sample_df
from .profiler import profile_columns
from .quality_checks import quality_warnings, duplicate_analysis
from .report_xlsx import write_report_xlsx
from .report_html import write_report_html

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")

def run():
    ensure_dir(OUTPUT_DIR)

    path = pick_excel_file()
    if not path:
        print("Dosya seçilmedi. Çıkılıyor.")
        return

    stamp = now_stamp()
    base_name = os.path.splitext(os.path.basename(path))[0]
    out_xlsx = os.path.join(OUTPUT_DIR, f"{base_name}_report_{stamp}.xlsx")
    out_html = os.path.join(OUTPUT_DIR, f"{base_name}_report_{stamp}.html")

    sheets_data = read_excel_all_sheets(path)

    sheet_rows = []
    all_profiles = []
    all_warnings = []
    all_dups = []

    sampling_any = False

    for sheet_name, info in sheets_data.items():
        df = info["df"]
        header_row = info["header_row"]

        df_for_profile, sampled = sample_df(df)
        sampling_any = sampling_any or sampled

        sheet_rows.append({
            "sheet_adi": sheet_name,
            "satir_sayisi": int(len(df)),
            "sutun_sayisi": int(df.shape[1]),
            "header_satiri": int(header_row),
        })

        prof = profile_columns(sheet_name, df_for_profile)
        all_profiles.append(prof)

        warns = quality_warnings(sheet_name, df_for_profile, prof)
        all_warnings.append(warns)

        dups = duplicate_analysis(sheet_name, df_for_profile)
        all_dups.append(dups)

    sheet_list_df = pd.DataFrame(sheet_rows)
    col_profile_df = pd.concat(all_profiles, ignore_index=True) if all_profiles else pd.DataFrame()
    warnings_df = pd.concat(all_warnings, ignore_index=True) if all_warnings else pd.DataFrame()
    dup_df = pd.concat(all_dups, ignore_index=True) if all_dups else pd.DataFrame()

    total_rows = int(sheet_list_df["satir_sayisi"].sum()) if len(sheet_list_df) else 0
    total_cols = int(sheet_list_df["sutun_sayisi"].sum()) if len(sheet_list_df) else 0
    warn_count = int((warnings_df["seviye"] == "WARN").sum()) if len(warnings_df) else 0
    err_count = int((warnings_df["seviye"] == "ERROR").sum()) if len(warnings_df) else 0

    genel_ozet = pd.DataFrame([{
        "dosya": os.path.basename(path),
        "sheet_sayisi": int(len(sheet_list_df)),
        "toplam_satir": total_rows,
        "toplam_kolon": total_cols,
        "warn_sayisi": warn_count,
        "error_sayisi": err_count,
        "ornekleme": "EVET" if sampling_any else "HAYIR"
    }])

    write_report_xlsx(out_xlsx, genel_ozet, sheet_list_df, col_profile_df, warnings_df, dup_df)

    cards = [
        {"label": "Sheet sayısı", "value": len(sheet_list_df)},
        {"label": "Toplam satır", "value": total_rows},
        {"label": "Toplam kolon", "value": total_cols},
        {"label": "WARN", "value": warn_count},
        {"label": "ERROR", "value": err_count},
    ]

    sheets_ctx = [{
        "sheet": r["sheet_adi"],
        "rows": r["satir_sayisi"],
        "cols": r["sutun_sayisi"],
        "header_row": r["header_satiri"],
    } for r in sheet_rows]

    if len(warnings_df):
        crit = warnings_df[warnings_df["seviye"].isin(["ERROR","WARN"])].head(15)
    else:
        crit = pd.DataFrame(columns=["seviye","sheet_adi","kolon_adi","konu","detay"])

    warnings_ctx = []
    for _, w in crit.iterrows():
        warnings_ctx.append({
            "seviye": w.get("seviye",""),
            "sheet": w.get("sheet_adi",""),
            "kolon": w.get("kolon_adi",""),
            "konu": w.get("konu",""),
            "detay": w.get("detay",""),
        })

    context = {
        "file_name": os.path.basename(path),
        "run_time": stamp,
        "sampling_note": "Büyük sheet’lerde örnekleme kullanıldı." if sampling_any else "Örnekleme kullanılmadı.",
        "cards": cards,
        "sheets": sheets_ctx,
        "warnings": warnings_ctx
    }

    write_report_html(TEMPLATE_DIR, "report_template.html", out_html, context)

    print("Bitti ✅")
    print("Excel raporu:", out_xlsx)
    print("HTML raporu :", out_html)

if __name__ == "__main__":
    run()
