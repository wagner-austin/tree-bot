from __future__ import annotations

import pandas as pd


def derive_matchscore(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["MatchScore"] = pd.to_numeric(out["Match1.Quality"], errors="coerce")
    return out
