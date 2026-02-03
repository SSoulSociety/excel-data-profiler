from __future__ import annotations
import pandas as pd


def _cell_to_str(x) -> str:
    if x is None:
        return ""
    try:
        if pd.isna(x):
            return ""
    except Exception:
        pass
    return str(x).strip()

def score_row(row_values: list[str]) -> float:
    vals = [v for v in row_values if v != ""]
    non_empty = len(vals)
    if non_empty == 0:
        return -1e9

    # text ratio
    text_like = 0
    for v in vals:
        has_alpha = any(ch.isalpha() for ch in v)
        if has_alpha:
            text_like += 1
    text_ratio = text_like / non_empty

    # uniqueness ratio
    uniq_ratio = len(set(vals)) / non_empty if non_empty else 0.0

    # long text penalty (header genelde paragraf olmaz)
    avg_len = sum(len(v) for v in vals) / non_empty
    length_penalty = 0.0
    if avg_len > 30:
        length_penalty = (avg_len - 30) / 30.0

    # fake header penalty: Column1, Column2, Unnamed
    fake_cnt = 0
    for v in vals:
        vv = v.strip()
        if vv.lower().startswith("unnamed"):
            fake_cnt += 1
        if vv.lower().startswith("column"):
            # Column1, Column2 ...
            tail = vv[6:].strip()
            if tail.isdigit():
                fake_cnt += 1
    fake_ratio = fake_cnt / non_empty

    score = 0.0
    score += non_empty * 2.0
    score += text_ratio * 10.0
    score += uniq_ratio * 6.0
    score -= length_penalty * 6.0
    score -= fake_ratio * 18.0  # sahte headerlari sert dusur

    return score


def detect_header_row(preview_df: pd.DataFrame, max_rows: int = 30) -> tuple[int, float]:
    n = min(len(preview_df), max_rows)
    if n == 0:
        return 0, 0.0

    scores = []

    def non_empty_count(row) -> int:
        cnt = 0
        for x in row:
            s = _cell_to_str(x)
            if s != "":
                cnt += 1
        return cnt

    for i in range(n):
        row = preview_df.iloc[i].tolist()
        row_strs = [_cell_to_str(x) for x in row]
        base = score_row(row_strs)

        # follow-up: header altinda data gelmeli, bos satir gelirse penalti
        next_rows = []
        for j in range(i + 1, min(n, i + 4)):  # sonraki 3 satir
            next_rows.append(non_empty_count(preview_df.iloc[j].tolist()))
        after_mean = (sum(next_rows) / len(next_rows)) if next_rows else 0.0

        # bos run: headerdan sonra ardarda tamamen bos satir var mi?
        empty_run = 0
        for j in range(i + 1, n):
            if non_empty_count(preview_df.iloc[j].tolist()) == 0:
                empty_run += 1
            else:
                break

        penalty = 0.0
        if after_mean < 2:
            penalty += 8.0
        if empty_run >= 2:
            penalty += 12.0

        scores.append(base - penalty)

    best_i = int(max(range(len(scores)), key=lambda k: scores[k]))
    best_score = scores[best_i]

    sorted_scores = sorted(scores)
    mid = sorted_scores[len(sorted_scores) // 2]
    gap = best_score - mid

    if best_score <= 0:
        conf = 0.0
    else:
        conf = max(0.0, min(1.0, gap / 15.0))

    return best_i, conf
