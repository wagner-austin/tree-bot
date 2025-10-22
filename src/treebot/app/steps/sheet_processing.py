from __future__ import annotations

import logging

import pandas as pd

from ...services.io_excel import InputSheet
from ...services.validate_service import ValidateService


def process_sheet(
    val: ValidateService,
    sh: InputSheet,
    logger: logging.Logger,
    species_map: dict[tuple[str, str], str] | None = None,
) -> pd.DataFrame:
    """Normalize headers and basic cleanup."""
    df = val.normalize_headers(sh.df.copy(), sh.schema)
    df["Sheet"] = sh.name

    # Fill down identity columns within the sheet: DataFolderName, CartridgeNum (skip DateRun)
    try:
        df, fill_counts, examples, example_values = val.forward_fill_identities(df)
        total_filled = sum(fill_counts.values())
        if total_filled:
            parts: list[str] = []
            if fill_counts.get("DataFolderName", 0):
                parts.append(f"DataFolderName: {fill_counts['DataFolderName']}")
            if fill_counts.get("CartridgeNum", 0):
                parts.append(f"CartridgeNum: {fill_counts['CartridgeNum']}")
            if parts:
                logger.info(f"Sheet '{sh.name}': forward-filled " + ", ".join(parts))
                # Show first few row indices per column as examples
                for col in ("DataFolderName", "CartridgeNum"):
                    idxs = examples.get(col) or []
                    vals = example_values.get(col) or []
                    if fill_counts.get(col, 0) and idxs:
                        pairs = ", ".join(f"{i}='{v}'" for i, v in list(zip(idxs, vals))[:5])
                        logger.info(f"  {col} examples (first 5): {pairs}")
    except Exception:
        # Non-fatal: continue without fill-down if any unexpected issue
        pass

    # Basic cleanup
    if "CartridgeNum" in df.columns:
        df = val.trim_cartridge(df)
    # Species mapping (do not overwrite existing values)
    if species_map is not None:
        try:
            df, filled, species_examples = val.apply_species_mapping(df, sh.name, species_map)
            if filled:
                logger.info(f"Sheet '{sh.name}': filled Species via mapping: {filled} rows")
                if species_examples:
                    sample = ", ".join(f"{i} '{c}' -> '{s}'" for (i, c, s) in species_examples[:5])
                    logger.info(f"  examples: {sample}")
        except Exception:
            # Non-fatal: continue without species fill if any unexpected issue
            pass
    if "DateRun" in df.columns:
        df, warnings = val.parse_dates_to_iso(df)
        if warnings:
            logger.warning(f"Sheet '{sh.name}': {len(warnings)} date parsing issues")
            for warning in warnings[:5]:  # Show first 5 warnings
                logger.warning(f"  {warning}")

    return df
