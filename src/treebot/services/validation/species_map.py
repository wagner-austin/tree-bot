from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, Mapping, Optional, Tuple, MutableMapping

import pandas as pd


# Canonical headers we support from the mapping workbook
_HEADER_ALIASES: Mapping[str, str] = {
    "sample.num": "SampleNumber",
    "samplenumber": "SampleNumber",
    "sample": "SampleNumber",
    "reserve": "Site",
    "site": "Site",
    "plant.species": "PlantSpecies",
    "plantspecies": "PlantSpecies",
    "species": "PlantSpecies",
    "date": "Date",
    "cartridge": "CartridgeNum",
    "cartridgenum": "CartridgeNum",
}


def _norm_header(name: str) -> str:
    return re.sub(r"[^a-z]", "", name.lower())


def _rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    ren: MutableMapping[str, str] = {}
    for col in df.columns:
        key = _norm_header(str(col))
        if key in _HEADER_ALIASES:
            ren[str(col)] = _HEADER_ALIASES[key]
    if ren:
        return df.rename(columns=ren)
    return df


def _strip_to_str(x: object) -> Optional[str]:
    if x is None:
        return None
    s = str(x).strip()
    return s if s else None


def _norm_site_token(s: str) -> str:
    return re.sub(r"[^a-z]", "", s.lower())


# Site tokens to canonical site keys used for joining
_SITE_TOKEN_TO_KEY: Mapping[str, str] = {
    # Emerson Oaks
    "emerson": "emerson",
    "emersonoaks": "emerson",
    # Stunt Ranch
    "stunt": "stunt",
    "stuntranch": "stunt",
    # Rancho
    "rancho": "rancho",
    # Fort Ord
    "fortord": "fortord",
    "for tord": "fortord",
    # Blue Oak
    "blueoak": "blueoak",
    # Point Reyes
    "pointreyes": "pointreyes",
    # Angelo
    "angelo": "angelo",
    # Lassen
    "lassen": "lassen",
    # Sagehen
    "sagehen": "sagehen",
    # Yosemite
    "yosemite": "yosemite",
}


def site_key_from_sheet_name(sheet_name: str) -> Optional[str]:
    token = _norm_site_token(sheet_name)
    return _SITE_TOKEN_TO_KEY.get(token)


def site_key_from_mapping_value(site_value: str) -> Optional[str]:
    token = _norm_site_token(site_value)
    return _SITE_TOKEN_TO_KEY.get(token)


def _iter_mapping_frames(path: Path) -> Iterable[pd.DataFrame]:
    if path.suffix.lower() in {".xlsx", ".xls"}:
        xls = pd.ExcelFile(path)
        for name in xls.sheet_names:
            try:
                df = pd.read_excel(xls, sheet_name=name)
                yield df
            except Exception:
                continue
    else:
        # Try CSV/TSV fallback by delimiter sniff
        try:
            yield pd.read_csv(path)
        except Exception:
            # Last resort: treat as TSV
            yield pd.read_csv(path, sep="\t")


def load_species_map(path: Path) -> Tuple[Mapping[Tuple[str, str], str], list[Tuple[str, str]]]:
    """Load (Site, CartridgeNum) -> PlantSpecies mapping from workbook.

    - Accepts multiple sheets; applies header aliasing (old -> canonical)
    - Normalizes Site to a site key; trims strings
    - Returns (map, ambiguous_keys)
    - Ambiguous keys are (site_key, cartridge) pairs with conflicting PlantSpecies
    """
    mapping: MutableMapping[Tuple[str, str], str] = {}
    conflicts: MutableMapping[Tuple[str, str], set[str]] = {}

    for raw in _iter_mapping_frames(path):
        df = _rename_columns(raw)
        # Only proceed if required columns exist
        if not {"Site", "CartridgeNum", "PlantSpecies"}.issubset(set(df.columns)):
            continue
        sub = df[["Site", "CartridgeNum", "PlantSpecies"]].copy()
        # Trim and normalize
        sub["Site"] = sub["Site"].map(_strip_to_str)
        sub["CartridgeNum"] = sub["CartridgeNum"].map(_strip_to_str)
        sub["PlantSpecies"] = sub["PlantSpecies"].map(_strip_to_str)
        sub = sub.dropna(subset=["Site", "CartridgeNum", "PlantSpecies"])

        for _, row in sub.iterrows():
            site_raw = str(row["Site"])  # already non-null
            site_key = site_key_from_mapping_value(site_raw)
            if site_key is None:
                continue
            cart = str(row["CartridgeNum"])  # already non-null
            sp = str(row["PlantSpecies"])  # already non-null
            key = (site_key, cart)
            if key not in mapping:
                mapping[key] = sp
                conflicts.setdefault(key, set()).add(sp)
            else:
                # Track potential conflicts
                conflicts.setdefault(key, set()).add(sp)

    ambiguous: list[Tuple[str, str]] = []
    # Remove ambiguous keys with differing species
    for key, vals in conflicts.items():
        if len(vals) > 1:
            ambiguous.append(key)
            if key in mapping:
                del mapping[key]

    return mapping, ambiguous


def apply_species_mapping(
    df: pd.DataFrame,
    site_key: str,
    species_map: Mapping[Tuple[str, str], str],
) -> Tuple[pd.DataFrame, int, list[Tuple[int, str, str]]]:
    """Fill Species for rows missing it using (site_key, CartridgeNum) map.

    - Does not overwrite existing non-empty Species values
    - Returns (new_df, filled_count, examples[(row_index, cartridge, species)])
    """
    if "CartridgeNum" not in df.columns:
        return df.copy(), 0, []

    out = df.copy()
    if "Species" not in out.columns:
        out["Species"] = pd.NA

    # Identify rows where Species is empty and CartridgeNum is present
    s_species = out["Species"]
    s_cart = out["CartridgeNum"].astype(str)
    empty_species = s_species.isna() | (s_species.astype(str).str.strip() == "")
    have_cart = s_cart.str.strip() != ""
    candidates = out.index[empty_species & have_cart].tolist()

    filled_examples: list[Tuple[int, str, str]] = []
    filled_count = 0
    for idx in candidates:
        cart_val = s_cart.at[idx].strip()
        key = (site_key, cart_val)
        sp = species_map.get(key)
        if sp is not None:
            out.at[idx, "Species"] = sp
            if filled_count < 5:
                filled_examples.append((int(idx), cart_val, sp))
            filled_count += 1

    return out, filled_count, filled_examples
