from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class Config:
    pipeline_version: str = "v1.0"
    certainty_threshold: int = 80
    frequency_min: int = 2
    site_mode: str = "sheetname"
    strict_fail: bool = True
    make_per_species_sheets: bool = True
    max_errors: int = 50
    # Pipeline stage: 'full' (default) or 'headers' for headers-only validation
    pipeline_stage: str = "full"


def load_config(path: Optional[Path], overrides: Optional[Dict[str, Any]] = None) -> Config:
    import yaml

    data: Dict[str, Any] = {}

    # Always load configs/config.yaml if it exists
    default_config = Path("configs/config.yaml")
    if default_config.exists():
        raw = yaml.safe_load(default_config.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            data.update(raw)

    # Then load custom config if provided (overrides default)
    if path is not None and path.exists():
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            data.update(raw)

    # Finally apply CLI overrides
    if overrides:
        data.update({k: v for k, v in overrides.items() if v is not None})

    # Coerce booleans from strings if needed (Windows/CLI friendliness)
    for key in ("strict_fail", "make_per_species_sheets"):
        if key in data and isinstance(data[key], str):
            data[key] = data[key].strip().lower() in {"1", "true", "yes", "y"}
    return Config(**data)
