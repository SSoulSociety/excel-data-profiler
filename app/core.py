from __future__ import annotations

import os
import pandas as pd

from .excel_reader import read_excel_all_sheets
from .sampler import sample_df
from .profiler import profile_columns
from .quality_checks import quality_warnings, duplicate_analysis
from .report_xlsx import write_report_xlsx
from .report_html import write_report_html


def generate_reports(
    excel_path: str,
    output_dir: str,
    template_dir: str,
    template_name: str = "report_template.html",
    sample_threshold: int = 200_000,
    sample_n_each: int = 5_000,
    log_cb=None,  # UI'ye log basmak için callback
) -> dict:
    """
    Excel'den rapor üretir: report.xlsx + report.html
    Büyük tablolarda örnekleme yapar.
    """

    def log(msg: str):
        if callable(log_cb):
            log_cb(msg)

    # Çıktı klasörü hazırla
    os.makedirs(output_dir, exist_ok=True)

    # Çıktı dosya adları
    base_name = os.path.splitext(os.path.basename(excel_path))[0]
    stamp = pd.Timestamp.now().strftime("%Y-%m-%d_%H-%M-%S")

    out_xlsx = os.path.join(output_dir, f"{base_name}_report_{stamp}.xlsx")
    out_html = os.path.join(output_dir, f"{base_name}_report_{stamp}.html")

    # Excel oku
    log("Excel okunuyor...")
    sheets_data = read_excel_all_sheets(excel_path)
    log(f"{len(sheets_data)} sheet bulundu.")

    sheet_rows = []
    all_profiles = []
    all_warnings = []
    all_dups = []
    sampling_any = False

    for sheet_name, info in sheets_data.items():
        df = info["df"]
        header_row = info.get("header_row", 1)

        log(f"Sheet işleniyor: {sheet_name} (satır={len(df)}, sütun={df.shape[1]})")

        # Big data örnekleme
        df_for_profile, sampled = sample_df(df, threshold=sample_threshold, n_each=sample_n_each)
        sampling_any = sampling_any or sampled

        sheet_rows.append({
            "sheet_adi": sheet_name,
            "satir_sayisi": int(len(df)),
            "sutun_sayisi": int(df.shape[1]),
            "header_satiri": int(header_row),
        })

        # Kolon profili
        prof = profile_columns(sheet_name, df_for_profile)
        all_profiles.append(prof)

        # Kalite uyarıları
        warns = quality_warnings(sheet_name, df_for_profile, prof)
        all_warnings.append(warns)

        # Duplicate analizi
        dups = duplicate_analysis(sheet_name, df_for_profile)
        all_dups.append(dups)

    # Birleştir
    sheet_list_df = pd.DataFrame(sheet_rows)
    col_profile_df = pd.concat(all_profiles, ignore_index=True) if all_profiles else pd.DataFrame()
    warnings_df = pd.concat(all_warnings, ignore_index=True) if all_warnings else pd.DataFrame()
    dup_df = pd.concat(all_dups, ignore_index=True) if all_dups else pd.DataFrame()

    # Genel özet metrikleri
    total_rows = int(sheet_list_df["satir_sayisi"].sum()) if len(sheet_list_df) else 0
    total_cols = int(sheet_list_df["sutun_sayisi"].sum()) if len(sheet_list_df) else 0
    warn_count = int((warnings_df["seviye"] == "WARN").sum()) if len(warnings_df) else 0
    err_count = int((warnings_df["seviye"] == "ERROR").sum()) if len(warnings_df) else 0

    genel_ozet = pd.DataFrame([{
        "dosya": os.path.basename(excel_path),
        "sheet_sayisi": int(len(sheet_list_df)),
        "toplam_satir": total_rows,
        "toplam_kolon": total_cols,
        "warn_sayisi": warn_count,
        "error_sayisi": err_count,
        "ornekleme": "EVET" if sampling_any else "HAYIR",
    }])

    # Excel raporunu yaz
    log("report.xlsx yazılıyor...")
    write_report_xlsx(out_xlsx, genel_ozet, sheet_list_df, col_profile_df, warnings_df, dup_df)

    # HTML raporu yaz
    log("report.html yazılıyor...")

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
        crit = warnings_df[warnings_df["seviye"].isin(["ERROR", "WARN"])].head(15)
    else:
        crit = pd.DataFrame(columns=["seviye", "sheet_adi", "kolon_adi", "konu", "detay"])

    warnings_ctx = []
    for _, w in crit.iterrows():
        warnings_ctx.append({
            "seviye": w.get("seviye", ""),
            "sheet": w.get("sheet_adi", ""),
            "kolon": w.get("kolon_adi", ""),
            "konu": w.get("konu", ""),
            "detay": w.get("detay", ""),
        })

    context = {
        "file_name": os.path.basename(excel_path),
        "run_time": stamp,
        "sampling_note": "Büyük sheet’lerde örnekleme kullanıldı." if sampling_any else "Örnekleme kullanılmadı.",
        "cards": cards,
        "sheets": sheets_ctx,
        "warnings": warnings_ctx,
    }

    write_report_html(template_dir, template_name, out_html, context)

    log("Bitti ✅")

    return {
        "out_xlsx": out_xlsx,
        "out_html": out_html,
        "summary": {
            "sheet_sayisi": int(len(sheet_list_df)),
            "toplam_satir": total_rows,
            "toplam_kolon": total_cols,
            "warn": warn_count,
            "error": err_count,
            "ornekleme": sampling_any,
        }
    }
