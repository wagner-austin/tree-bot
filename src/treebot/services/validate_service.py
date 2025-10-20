from __future__ import annotations

import logging
from pathlib import Path
from typing import Tuple

import pandas as pd

from ..services.io_excel import SchemaName
from .validation.headers import normalize_headers
from .validation.dates import parse_dates_to_iso
from .validation.keys import trim_cartridge
from .validation.class_map import load_class_map


class ValidateService:
    """Lightweight service for header normalization and basic cleanup."""

    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger

    def normalize_headers(self, df: pd.DataFrame, schema: SchemaName) -> pd.DataFrame:
        return normalize_headers(df, schema)

    def parse_dates_to_iso(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, list[str]]:
        """Parse dates to ISO format. Returns (df, warnings)."""
        return parse_dates_to_iso(df)

    def trim_cartridge(self, df: pd.DataFrame) -> pd.DataFrame:
        return trim_cartridge(df)

    def load_class_map(self, path: Path) -> dict[str, str]:
        self.logger.info("Loading classes map", extra={"path": str(path)})
        return load_class_map(path)
