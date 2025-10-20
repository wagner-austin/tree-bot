from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from ..utils.logging_setup import setup_logging


@dataclass(frozen=True)
class RunContext:
    run_dir: Path
    logger: logging.Logger


def start_run(out_dir: Path, base_logger_name: str = "treebot") -> RunContext:
    run_dir = out_dir / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    setup_logging(run_dir)
    logger = logging.getLogger(base_logger_name)
    logger.info("Run started", extra={"run_dir": str(run_dir)})
    return RunContext(run_dir=run_dir, logger=logger)
