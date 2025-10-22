from __future__ import annotations

from typing import List, Mapping, Tuple

import pandas as pd

from ...domain.errors import ValidationIssue
from .compound_class import derive_compound_and_class
from .matchscore import derive_matchscore


def old_to_new(
    df_old: pd.DataFrame,
    class_map: Mapping[str, str],
) -> Tuple[pd.DataFrame, List[ValidationIssue], pd.DataFrame]:
    """
    Transform old schema to new schema:
    1. Add empty Species column if not present
    2. Derive Compound + Class from Match1\n    3. Derive MatchScore from Match1.Quality
    """
    df = df_old.copy()
    if "Species" not in df.columns:
        df["Species"] = pd.NA

        # Derive Compound + Class
    with_compound, issues, unmapped = derive_compound_and_class(df, class_map)

    # Derive MatchScore
    final = derive_matchscore(with_compound)

    # Add Comments if missing
    if "Comments" not in final.columns:
        final["Comments"] = pd.NA

    return final, issues, unmapped
