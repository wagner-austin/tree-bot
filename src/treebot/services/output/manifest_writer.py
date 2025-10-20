from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

import pandas as pd

from ...config import Config
from .utils import sha256_file


def write_manifest(
    *,
    run_dir: Path,
    input_path: Path,
    classes_path: Path,
    started_at: str,
    finished_at: str,
    cfg: Config,
    logger: logging.Logger,
) -> None:
    import platform
    import sys
    import yaml

    inputs: Dict[str, Dict[str, str]] = {
        "results": {"path": str(input_path), "sha256": sha256_file(input_path)},
        "classes": {"path": str(classes_path), "sha256": sha256_file(classes_path)},
    }

    manifest: Dict[str, Any] = {
        "pipeline_version": cfg.pipeline_version,
        "started_at": started_at,
        "finished_at": finished_at,
        "inputs": inputs,
        "parameters": {
            "certainty_threshold": cfg.certainty_threshold,
            "frequency_min": cfg.frequency_min,
            "site_mode": cfg.site_mode,
            "strict_fail": cfg.strict_fail,
            "make_per_species_sheets": cfg.make_per_species_sheets,
            "max_errors": cfg.max_errors,
        },
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "pandas": pd.__version__,
        },
    }

    out_path = run_dir / "run_manifest.yaml"
    logger.info("Writing run_manifest.yaml", extra={"path": str(out_path)})
    with out_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(manifest, f, sort_keys=False, allow_unicode=True)
