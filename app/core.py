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
    auto_header: bool = False,
    log_cb=None,  # UI'ye log basmak iç in callback
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
    log(f"auto_header={auto_header}")
    log("Excel okunuyor...")
    sheets_data = read_excel_all_sheets(excel_path, auto_header=auto_header)
    log(f"{len(sheets_data)} sheet bulundu.")

    sheet_rows = []
    all_profiles = []   
    all_warnings = []
    all_dups = []
    sampling_any = False

    for sheet_name, info in sheets_data.items():
        df = info["df"]
        header_row = info.get("header_row", 1)

        log(f"Sheet isleniyor: {sheet_name} (satir={len(df)}, sutun={df.shape[1]}, header_satiri={header_row})")

        # Big data örnekleme
        df_for_profile, sampled = sample_df(df, threshold=sample_threshold, n_each=sample_n_each)
        sampling_any = sampling_any or sampled

        sheet_rows.append({
            "sheet_adi": sheet_name,
            "satir_sayisi": int(len(df)),
            "sutun_sayisi": int(df.shape[1]),
            "header_satiri": int(header_row),
            "header_confidence": float(info.get("header_confidence", 0.0)),
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

    # Benzersiz kolon sayisi (bos ve 'Unnamed' kolonlari hariç)
    unique_cols = set()

    for info in sheets_data.values():
        df0 = info["df"]

        cols = []
        for c in df0.columns:
            if c is None:
                continue

            c_str = str(c).strip()
            if not c_str:
                continue

            if c_str.lower().startswith("unnamed"):
                continue

            cols.append(c_str)

        unique_cols.update(cols)

    total_unique_cols = len(unique_cols)


    # Genel özet metrikleri
    total_rows = int(sheet_list_df["satir_sayisi"].sum()) if len(sheet_list_df) else 0
    total_cols = int(sheet_list_df["sutun_sayisi"].sum()) if len(sheet_list_df) else 0
    if len(warnings_df) and "seviye" in warnings_df.columns:
        warn_count = int((warnings_df["seviye"] == "WARN").sum())
        err_count  = int((warnings_df["seviye"] == "ERROR").sum())
    else:
        warn_count = 0
        err_count = 0

    genel_ozet = pd.DataFrame([{
        "dosya": os.path.basename(excel_path),
        "sheet_sayisi": int(len(sheet_list_df)),
        "toplam_satir": total_rows,
        "toplam_kolon": total_cols,
        "benzersiz_kolon": total_unique_cols,
        "warn_sayisi": warn_count,
        "error_sayisi": err_count,
        "ornekleme": "EVET" if sampling_any else "HAYIR",
    }])

    # Excel raporunu yaz
    log("report.xlsx yaziliyor...")
    write_report_xlsx(out_xlsx, genel_ozet, sheet_list_df, col_profile_df, warnings_df, dup_df)

    # HTML raporu yaz
    log("report.html yaziliyor...")

    cards = [
        {"label": "Sheet sayisi", "value": len(sheet_list_df)},
        {"label": "Toplam satir", "value": total_rows},
        {"label": "Toplam kolon", "value": total_cols},
        {"label": "WARN", "value": warn_count},
        {"label": "ERROR", "value": err_count},
        {"label": "Benzersiz kolon", "value": total_unique_cols},
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
    # -----------------------------
    # Charts + HTML dashboard data
    # -----------------------------

    # chart: sheet sizes
    sheet_labels = [r["sheet_adi"] for r in sheet_rows]
    sheet_row_counts = [int(r["satir_sayisi"]) for r in sheet_rows]

    # chart: top missing columns (Top 10)
    top_missing_labels = []
    top_missing_values = []
    if len(col_profile_df) and "bos_oran" in col_profile_df.columns:
        tmp = col_profile_df.copy()
        tmp = tmp.sort_values("bos_oran", ascending=False).head(10)
        for _, rr in tmp.iterrows():
            sheet_adi = str(rr.get("sheet_adi", ""))
            kolon_adi = str(rr.get("kolon_adi", ""))
            label = f"{sheet_adi}::{kolon_adi}" if sheet_adi else kolon_adi
            top_missing_labels.append(label)
            try:
                # bos_oran sende yuzde (0-100). chartta da yuzde gosterecegiz.
                top_missing_values.append(float(rr.get("bos_oran", 0.0)))
            except Exception:
                top_missing_values.append(0.0)

    # chart: type distribution (counts)
    type_labels = []
    type_values = []
    if len(col_profile_df) and "tahmini_tip" in col_profile_df.columns:
        vc = col_profile_df["tahmini_tip"].fillna("unknown").astype(str).value_counts()
        type_labels = list(vc.index[:8])
        type_values = [int(v) for v in list(vc.values[:8])]

    charts = {
        "sheet_sizes": {"labels": sheet_labels, "values": sheet_row_counts},
        "top_missing": {"labels": top_missing_labels, "values": top_missing_values},
        "type_dist": {"labels": type_labels, "values": type_values},
    }

    # pick biggest sheet df for preview/KPIs
    biggest_name = None
    biggest_rows = -1
    for sn, info in sheets_data.items():
        dfi = info["df"]
        if len(dfi) > biggest_rows:
            biggest_rows = len(dfi)
            biggest_name = sn

    main_df = sheets_data[biggest_name]["df"] if biggest_name else None
    
    # KPIs + preview
    rows_count = 0
    cols_count = 0
    missing_total = 0
    missing_pct = 0.0
    dup_rows = 0
    preview_cols = []
    preview_rows = []

    if main_df is not None:
        rows_count = int(main_df.shape[0])
        cols_count = int(main_df.shape[1])

        try:
            missing_total = int(main_df.isna().sum().sum())
            total_cells = max(1, rows_count * max(1, cols_count))
            missing_pct = round((missing_total / total_cells) * 100, 2)
        except Exception:
            missing_total = 0
            missing_pct = 0.0

        try:
            dup_rows = int(main_df.duplicated().sum())
        except Exception:
            dup_rows = 0

        try:
            preview_df = main_df.head(15).copy()
            preview_cols = [str(c) for c in list(preview_df.columns)[:20]]
            preview_rows = preview_df[preview_cols].fillna("").astype(str).to_dict(orient="records")
        except Exception:
            preview_cols = []
            preview_rows = []

    kpis = {
        "rows": rows_count,
        "cols": cols_count,
        "missing_total": missing_total,
        "missing_pct": missing_pct,
        "dup_rows": dup_rows,
    }

    if sampling_any:
        sampling_note = (
            f"Buyuk sheetler orneklenerek analiz edildi "
            f"(esik={sample_threshold}, her tip icin ornek={sample_n_each})."
        )
    else:
        sampling_note = "Tum satirlar analiz edildi, ornekleme kullanilmadi."

    # top issues (simdilik warnings'dan ilk 8)
    top_issues = []
    if len(warnings_df):
        tmpw = warnings_df[warnings_df["seviye"].isin(["ERROR", "WARN"])].head(8)
        for _, w in tmpw.iterrows():
            sev = str(w.get("seviye", ""))
            sh = str(w.get("sheet_adi", ""))
            ko = str(w.get("kolon_adi", ""))
            konu = str(w.get("konu", ""))
            top_issues.append(f"{sev}: {sh} / {ko} - {konu}")

    context = {
        "file_name": os.path.basename(excel_path),
        "run_time": stamp,
        "sampling_note": sampling_note,
        "cards": cards,
        "sheets": sheets_ctx,
        "warnings": warnings_ctx,
        "charts": charts,
        "kpis": kpis,
        "preview_cols": preview_cols,
        "preview_rows": preview_rows,
        "top_issues": top_issues,
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
