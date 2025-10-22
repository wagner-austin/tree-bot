from __future__ import annotations

import logging
from pathlib import Path
from typing import Tuple

import pandas as pd

from ..services.io_excel import SchemaName
from .validation.headers import normalize_headers
from .validation.dates import parse_dates_to_iso
from .validation.keys import trim_cartridge, forward_fill_columns
from .validation.species_map import (
    apply_species_mapping,
    load_species_map as _load_species_map,
    site_key_from_sheet_name,
)
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

    def forward_fill_identities(
        self, df: pd.DataFrame
    ) -> tuple[
        pd.DataFrame,
        dict[str, int],
        dict[str, list[int]],
        dict[str, list[str]],
    ]:
        """Forward-fill DataFolderName and CartridgeNum within each sheet.

        Treats blanks/whitespace as missing for fill purposes.
        Does not touch DateRun (explicitly skipped as per requirements).
        Returns (df, counts) with per-column fill counts.
        """
        cols = [c for c in ["DataFolderName", "CartridgeNum"] if c in df.columns]
        if not cols:
            return (
                df.copy(),
                {"DataFolderName": 0, "CartridgeNum": 0},
                {"DataFolderName": [], "CartridgeNum": []},
                {"DataFolderName": [], "CartridgeNum": []},
            )
        return forward_fill_columns(df, cols)

    def load_class_map(self, path: Path) -> dict[str, str]:
        self.logger.info("Loading classes map", extra={"path": str(path)})
        mp = load_class_map(path)
        self.logger.info("Loaded classes map", extra={"entries": len(mp)})
        return mp

    def load_species_map(
        self, path: Path
    ) -> tuple[dict[tuple[str, str], str], list[tuple[str, str]]]:
        self.logger.info("Loading species map", extra={"path": str(path)})
        mp, ambiguous = _load_species_map(path)
        self.logger.info(
            "Loaded species map",
            extra={"entries": len(mp), "ambiguous_keys": len(ambiguous)},
        )
        if ambiguous:
            # Log first few ambiguous keys
            for key in ambiguous[:5]:
                self.logger.warning(
                    "Species map ambiguity: duplicate (site, cartridge) with different species",
                    extra={"site": key[0], "cartridge": key[1]},
                )
        return mp, ambiguous

    def apply_species_mapping(
        self,
        df: pd.DataFrame,
        sheet_name: str,
        species_map: dict[tuple[str, str], str] | None,
    ) -> tuple[pd.DataFrame, int, list[tuple[int, str, str]]]:
        """Apply species mapping for a given sheet; no overwrite of existing values."""
        if not species_map:
            return df.copy(), 0, []
        site_key = site_key_from_sheet_name(sheet_name)
        if site_key is None:
            # Unknown site -> skip silently
            return df.copy(), 0, []
        return apply_species_mapping(df, site_key, species_map)
