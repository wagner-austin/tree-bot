from __future__ import annotations

import logging
from pathlib import Path

from treebot.config import Config
from treebot.services.output.manifest_writer import write_manifest


def test_write_manifest_creates_file(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    # Create dummy input/ classes files for hashing
    (tmp_path / "in.xlsx").write_bytes(b"0")
    (tmp_path / "classes.yaml").write_text("version: '1'\nmap: {}\n", encoding="utf-8")

    logger = logging.getLogger("test")
    write_manifest(
        run_dir=run_dir,
        input_path=tmp_path / "in.xlsx",
        classes_path=tmp_path / "classes.yaml",
        started_at="2024-01-01T00:00:00Z",
        finished_at="2024-01-01T00:01:00Z",
        cfg=Config(),
        logger=logger,
    )

    assert (run_dir / "run_manifest.yaml").exists()
