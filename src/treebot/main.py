from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .config import Config, load_config
from .app.container import build_container
from .app.orchestrator import Orchestrator


logger = logging.getLogger(__name__)


def _make_orchestrator(cfg: Config) -> Orchestrator:
    container = build_container("treebot", cfg)
    return Orchestrator(container=container, cfg=cfg, logger=logging.getLogger("treebot.main"))


def run_pipeline(
    input_path: Path,
    classes_path: Path,
    out_dir: Path,
    cfg: Config | None = None,
    mapping_path: Path | None = None,
) -> int:
    orch = _make_orchestrator(cfg or Config())
    return orch.run(input_path, classes_path, mapping_path, out_dir)


def main() -> int:
    ap = argparse.ArgumentParser(description="TreeBot CLI")
    ap.add_argument("--input", required=True, type=Path, help="Path to results workbook (xlsx)")
    ap.add_argument("--classes", required=True, type=Path, help="Path to classes.yaml")
    ap.add_argument(
        "--out", required=False, type=Path, default=Path("runs"), help="Output base dir"
    )
    ap.add_argument(
        "--mapping",
        required=False,
        type=Path,
        help="Optional species mapping workbook (Site, CartridgeNum -> PlantSpecies)",
    )
    ap.add_argument("--config", required=False, type=Path, help="Optional YAML config file")
    ap.add_argument(
        "--max-errors", required=False, type=int, default=50, help="Max errors to show in reports"
    )
    ap.add_argument(
        "--stage",
        required=False,
        choices=["full", "headers"],
        default=None,
        help="Pipeline stage: 'headers' to validate headers only, or 'full' (default)",
    )
    args = ap.parse_args()

    overrides = {"max_errors": args.max_errors}
    if args.stage:
        overrides["pipeline_stage"] = args.stage
    cfg = load_config(args.config, overrides=overrides)

    try:
        return run_pipeline(args.input, args.classes, args.out, cfg, args.mapping)
    except Exception as exc:  # pragma: no cover
        logging.basicConfig(level=logging.ERROR)
        logging.exception("Unhandled exception: %s", exc)
        return 3


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
