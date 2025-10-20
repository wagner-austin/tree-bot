from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from ..io_excel import SchemaName


_schema_config: dict[str, Any] | None = None


def _load_schema_config() -> dict[str, Any]:
    """Load schema.yaml once and cache it."""
    global _schema_config
    if _schema_config is None:
        schema_path = Path(__file__).parent.parent.parent.parent.parent / "configs" / "schema.yaml"
        with open(schema_path, "r", encoding="utf-8") as f:
            _schema_config = yaml.safe_load(f)
    return _schema_config


def normalize_headers(df: pd.DataFrame, schema: SchemaName) -> pd.DataFrame:
    """
    Normalize column headers:
    1. Strip unit suffixes like (min), (sec), (%)
    2. Apply column aliases (e.g., "Sample Type" → "Species")
    """
    config = _load_schema_config()
    rename_map: dict[str, str] = {}

    # Step 1: Strip unit suffixes from all columns
    strip_suffixes: list[str] = config["strip_suffixes"]
    for col in df.columns.astype(str):
        col_clean = col.strip()
        for suffix in strip_suffixes:
            if col_clean.endswith(suffix):
                col_clean = col_clean[: -len(suffix)].strip()
                break
        if col_clean != col:
            rename_map[col] = col_clean

    # Step 2: Apply column aliases
    aliases: dict[str, list[str]] = config["aliases"]
    alias_map: dict[str, str] = {}
    for canonical, variants in aliases.items():
        for variant in variants:
            alias_map[variant.lower()] = canonical

    # Check current columns (after suffix stripping) against aliases
    current_cols = [rename_map.get(c, c) for c in df.columns.astype(str)]

    for orig_col, current_col in zip(df.columns.astype(str), current_cols, strict=True):
        col_lower = current_col.lower().strip()
        if col_lower in alias_map:
            canonical = alias_map[col_lower]
            if canonical not in current_cols:
                rename_map[orig_col] = canonical

    return df.rename(columns=rename_map)
