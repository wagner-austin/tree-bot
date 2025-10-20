from __future__ import annotations

from typing import List, Mapping, Tuple, Optional

import pandas as pd

from ...domain.errors import ValidationIssue
from ...utils.normalize import normalize_text
from .compound_class import derive_compound_and_class
from .matchscore import derive_matchscore


def old_to_new(
    df_old: pd.DataFrame,
    class_map: Mapping[str, str],
    canon_map: Optional[Mapping[str, str]] = None,
) -> Tuple[pd.DataFrame, List[ValidationIssue], pd.DataFrame]:
    """
    Transform old schema to new schema:
    1. Add empty Species column if not present
    2. Apply optional name canonicalization to Match1
    3. Derive Compound + Class from Match1
    4. Derive MatchScore from Match1.Quality
    """
    df = df_old.copy()
    if "Species" not in df.columns:
        df["Species"] = pd.NA

    # Apply name canonicalization before class derivation, if provided
    if canon_map:

        def _norm_or_na(val: object) -> object:
            if pd.isna(val):
                return pd.NA
            s = str(val).strip()
            if not s:
                return pd.NA
            return normalize_text(s)

        comp_norm = df["Match1"].map(_norm_or_na)
        canon_norm = {normalize_text(k): normalize_text(v) for k, v in canon_map.items()}

        def _apply_canon(val: object) -> object:
            if pd.isna(val):
                return pd.NA
            return canon_norm.get(str(val), str(val))

        df["Match1"] = comp_norm.map(_apply_canon)

    # Derive Compound + Class
    with_compound, issues, unmapped = derive_compound_and_class(df, class_map)

    # Derive MatchScore
    final = derive_matchscore(with_compound)

    # Add Comments if missing
    if "Comments" not in final.columns:
        final["Comments"] = pd.NA

    return final, issues, unmapped
