from __future__ import annotations

import pandas as pd


def trim_cartridge(df: pd.DataFrame) -> pd.DataFrame:
    """Remove leading/trailing whitespace from CartridgeNum column."""
    df2 = df.copy()
    df2["CartridgeNum"] = df2["CartridgeNum"].astype(str).str.strip()
    return df2


def _forward_fill_series(
    s: pd.Series,
) -> tuple[pd.Series, int, list[int], list[str]]:
    """Forward-fill a Series where empty/whitespace is treated as missing.

    Returns (filled_series, filled_count, filled_indices), where filled_count is
    the number of positions that were empty-like and became non-empty due to the
    fill, and filled_indices are the index labels where a fill occurred.
    """
    # Treat empty strings/whitespace as missing for fill purposes
    empty_like = s.isna() | (s.astype(str).str.strip() == "")
    s2 = s.copy()
    s2 = s2.mask(empty_like, other=pd.NA)
    # Opt into pandas future behavior to avoid downcasting warning during ffill
    # and keep behavior stable across pandas versions.
    with pd.option_context("future.no_silent_downcasting", True):
        s3 = s2.ffill()
    # Additionally, infer objects to normalize dtype without copying.
    s3 = s3.infer_objects(copy=False)
    filled = (empty_like) & (s3.notna())
    try:
        idxs = [int(i) for i in s.index[filled].tolist()]
    except Exception:
        idxs = []

    # Provide sample filled values for logging (aligned with idxs order)
    samples: list[str] = []
    for i in idxs[:5]:
        try:
            samples.append(str(s3.loc[i]))
        except Exception:
            samples.append("")

    return s3, int(filled.sum()), idxs, samples


def forward_fill_columns(
    df: pd.DataFrame, columns: list[str]
) -> tuple[pd.DataFrame, dict[str, int], dict[str, list[int]], dict[str, list[str]]]:
    """Forward-fill selected columns, treating blanks as missing.

    - Only affects provided columns; no cross-column logic
    - First non-empty establishes value; top-of-column blanks remain blank
    - Returns (new_df, counts) where counts[col] = number of cells filled
    """
    df2 = df.copy()
    counts: dict[str, int] = {}
    examples: dict[str, list[int]] = {}
    example_values: dict[str, list[str]] = {}
    for col in columns:
        if col in df2.columns:
            filled_series, n, idxs, vals = _forward_fill_series(df2[col])
            df2[col] = filled_series
            counts[col] = n
            examples[col] = idxs
            example_values[col] = vals
        else:
            counts[col] = 0
            examples[col] = []
            example_values[col] = []
    return df2, counts, examples, example_values
