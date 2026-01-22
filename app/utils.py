from __future__ import annotations
import os
import datetime as dt

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def now_stamp() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def safe_str(x) -> str:
    try:
        return "" if x is None else str(x)
    except Exception:
        return ""
