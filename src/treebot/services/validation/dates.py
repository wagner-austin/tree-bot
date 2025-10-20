from __future__ import annotations

import re
from typing import Tuple

import pandas as pd


_ISO_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})(?:\s.+)?$")


def parse_dates_to_iso(df: pd.DataFrame) -> Tuple[pd.DataFrame, list[str]]:
    """
    Parse DateRun column to ISO format (YYYY-MM-DD).
    Accepts: M/D/YYYY or YYYY-MM-DD
    Returns: (DataFrame with parsed dates, list of warning messages)
    """
    warnings: list[str] = []
    isos: list[str | None] = []

    for i, v in enumerate(df["DateRun"].astype(str).tolist()):
        v = v.strip()
        if not v or v.lower() == "nan":
            warnings.append(f"Row {i}: DateRun is empty")
            isos.append(None)
            continue

        # Accept YYYY-MM-DD (ISO format)
        m1 = _ISO_DATE_RE.match(v)
        if m1:
            yy, mm, dd = int(m1.group(1)), int(m1.group(2)), int(m1.group(3))
            isos.append(f"{yy:04d}-{mm:02d}-{dd:02d}")
            continue

        # Accept M/D/YYYY
        try:
            m_s, d_s, y_s = v.split("/")
            mm = int(m_s)
            dd = int(d_s)
            yy = int(y_s)
            isos.append(f"{yy:04d}-{mm:02d}-{dd:02d}")
        except Exception:
            warnings.append(f"Row {i}: Unparseable DateRun '{v}' (expected M/D/YYYY or ISO)")
            isos.append(None)

    df2 = df.copy()
    df2["DateRun"] = isos
    return df2, warnings
