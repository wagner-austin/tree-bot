from __future__ import annotations

import logging
from pathlib import Path
from typing import cast

import pandas as pd

from ...config import Config
from .utils import sha256_file
from ...types import (
    Manifest,
    ManifestEnvironment,
    ManifestInputs,
    ManifestInputsEntry,
    ManifestParameters,
)


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

    inputs: ManifestInputs = {
        "results": cast(
            ManifestInputsEntry, {"path": str(input_path), "sha256": sha256_file(input_path)}
        ),
        "classes": cast(
            ManifestInputsEntry, {"path": str(classes_path), "sha256": sha256_file(classes_path)}
        ),
    }

    params: ManifestParameters = {
        "certainty_threshold": cfg.certainty_threshold,
        "frequency_min": cfg.frequency_min,
        "site_mode": cfg.site_mode,
        "strict_fail": cfg.strict_fail,
        "make_per_species_sheets": cfg.make_per_species_sheets,
        "max_errors": cfg.max_errors,
    }

    env: ManifestEnvironment = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "pandas": pd.__version__,
    }

    manifest: Manifest = {
        "pipeline_version": cfg.pipeline_version,
        "started_at": started_at,
        "finished_at": finished_at,
        "inputs": inputs,
        "parameters": params,
        "environment": env,
    }

    out_path = run_dir / "run_manifest.yaml"
    logger.info("Writing run_manifest.yaml", extra={"path": str(out_path)})
    with out_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(manifest, f, sort_keys=False, allow_unicode=True)
