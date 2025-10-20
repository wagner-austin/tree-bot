from __future__ import annotations

import logging

import pandas as pd

from ...services.io_excel import InputSheet
from ...services.validate_service import ValidateService


def process_sheet(val: ValidateService, sh: InputSheet, logger: logging.Logger) -> pd.DataFrame:
    """Normalize headers and basic cleanup."""
    df = val.normalize_headers(sh.df.copy(), sh.schema)
    df["Sheet"] = sh.name

    # Basic cleanup
    if "CartridgeNum" in df.columns:
        df = val.trim_cartridge(df)
    if "DateRun" in df.columns:
        df, warnings = val.parse_dates_to_iso(df)
        if warnings:
            logger.warning(f"Sheet '{sh.name}': {len(warnings)} date parsing issues")
            for warning in warnings[:5]:  # Show first 5 warnings
                logger.warning(f"  {warning}")

    return df
