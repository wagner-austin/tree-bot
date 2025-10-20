from __future__ import annotations

from typing import List, Mapping, Tuple

import pandas as pd

from ...domain.errors import ErrorCategory, ValidationIssue
from ...utils.normalize import normalize_text


def derive_compound_and_class(
    df: pd.DataFrame, class_map: Mapping[str, str]
) -> Tuple[pd.DataFrame, List[ValidationIssue], pd.DataFrame]:
    out = df.copy()
    issues: List[ValidationIssue] = []

    # Compound from Match1 (normalized); keep blanks as missing (pd.NA)
    def _to_compound(val: object) -> object:
        import pandas as pd  # local import

        if pd.isna(val):
            return pd.NA
        s = str(val).strip()
        if not s:
            return pd.NA
        return normalize_text(s)

    out["Compound"] = out["Match1"].map(_to_compound)

    # Class lookup
    out["Class"] = out["Compound"].map(lambda x: class_map.get(x))
    missing_class = out["Class"].isna()
    for i in out.index[missing_class].tolist():
        issues.append(
            ValidationIssue(
                category=ErrorCategory.MAPPING_MISSING,
                code="CLASS_MISSING",
                message="Compound missing in classes.yaml",
                row_index=int(i),
            )
        )

    unmapped_compounds = (
        out.loc[missing_class, ["Compound"]]
        .assign(count=1)
        .groupby("Compound", as_index=False)["count"]
        .sum()
        .sort_values(["count", "Compound"], ascending=[False, True])
    )
    return out, issues, unmapped_compounds
