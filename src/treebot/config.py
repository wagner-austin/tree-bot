from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, cast

from .types import ConfigOverrides, YamlConfig


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


def load_config(path: Optional[Path], overrides: Optional[ConfigOverrides] = None) -> Config:
    import yaml

    data: YamlConfig = {}

    # Always load configs/config.yaml if it exists
    default_config = Path("configs/config.yaml")
    if default_config.exists():
        raw = yaml.safe_load(default_config.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            data.update(cast(YamlConfig, raw))

    # Then load custom config if provided (overrides default)
    if path is not None and path.exists():
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            data.update(cast(YamlConfig, raw))

    # Finally apply CLI overrides
    if overrides:
        data.update(cast(YamlConfig, {k: v for k, v in overrides.items() if v is not None}))

    # Coerce booleans from strings if needed (Windows/CLI friendliness)
    for key in ("strict_fail", "make_per_species_sheets"):
        if key in data:
            val = data.get(key)
            if isinstance(val, str):
                data[key] = val.strip().lower() in {"1", "true", "yes", "y"}

    # Build Config explicitly with coercions for strict typing
    defaults = Config()
    cfg = Config(
        pipeline_version=str(data.get("pipeline_version", defaults.pipeline_version)),
        certainty_threshold=int(data.get("certainty_threshold", defaults.certainty_threshold)),
        frequency_min=int(data.get("frequency_min", defaults.frequency_min)),
        site_mode=str(data.get("site_mode", defaults.site_mode)),
        strict_fail=bool(data.get("strict_fail", defaults.strict_fail)),
        make_per_species_sheets=bool(
            data.get("make_per_species_sheets", defaults.make_per_species_sheets)
        ),
        max_errors=int(data.get("max_errors", defaults.max_errors)),
        pipeline_stage=str(data.get("pipeline_stage", defaults.pipeline_stage)),
    )
    return cfg
