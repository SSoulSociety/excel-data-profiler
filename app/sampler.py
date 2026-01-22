from __future__ import annotations
import pandas as pd

def sample_df(df: pd.DataFrame, threshold: int = 200_000, n_each: int = 5_000) -> tuple[pd.DataFrame, bool]:
    rows = len(df)
    if rows <= threshold:
        return df, False

    head = df.head(n_each)
    tail = df.tail(n_each)

    middle_count = max(0, rows - (len(head) + len(tail)))
    rand_n = min(n_each, middle_count)

    if rand_n > 0:
        mid = df.iloc[len(head): rows - len(tail)]
        rand = mid.sample(n=rand_n, random_state=42) if len(mid) > rand_n else mid
        out = pd.concat([head, rand, tail], ignore_index=True)
    else:
        out = pd.concat([head, tail], ignore_index=True)

    return out, True
