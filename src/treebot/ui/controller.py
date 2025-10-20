from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..config import Config
from ..main import run_pipeline


logger = logging.getLogger("treebot.ui.controller")


@dataclass(frozen=True)
class UiRunResult:
    code: int
    run_dir: Optional[Path]
    error: Optional[str] = None


def _list_run_dirs(base: Path) -> list[Path]:
    if not base.exists():
        return []
    return sorted([p for p in base.iterdir() if p.is_dir()])


class UiController:
    def __init__(self, base_logger: Optional[logging.Logger] = None) -> None:
        self.logger = base_logger or logging.getLogger("treebot.ui")

    def _latest_run_dir(self, out_base: Path, before: list[Path]) -> Optional[Path]:
        after = _list_run_dirs(out_base)
        new = [p for p in after if p not in before]
        if not new:
            return after[-1] if after else None
        return new[-1]

    def run(
        self,
        input_path: Path,
        classes_path: Path,
        out_dir: Path,
        cfg: Config | None,
    ) -> UiRunResult:
        try:
            cfg2 = cfg or Config()
            before = _list_run_dirs(out_dir)
            self.logger.info(
                "UI starting pipeline",
                extra={
                    "input": str(input_path),
                    "classes": str(classes_path),
                    "out": str(out_dir),
                },
            )
            code = run_pipeline(input_path, classes_path, out_dir, cfg2)
            run_dir = self._latest_run_dir(out_dir, before)
            return UiRunResult(code=code, run_dir=run_dir)
        except Exception as exc:
            self.logger.exception("UI pipeline error: %s", exc)
            return UiRunResult(code=3, run_dir=None, error=str(exc))
