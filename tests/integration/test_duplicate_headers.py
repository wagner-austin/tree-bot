from __future__ import annotations

from pathlib import Path

import pandas as pd

from treebot.main import run_pipeline


def test_duplicate_headers_fail_gracefully(tmp_path: Path) -> None:
    # Create a sheet with duplicate 'DateRun' header to trigger SCHEMA_ERROR
    old_header = [
        "DataFolderName",
        "DateRun",
        "DateRun",
        "CartridgeNum",
        "RetentionTime",
        "Match1",
        "Match1.Quality",
        "Match2",
        "Match2.Quality",
        "Match3",
        "Match3.Quality",
        "Comments (note here, for example, if there are common names and official IUPAC names that are actually the same compound)",
    ]
    old_row = [
        "DF1",
        "4/3/2025",
        "4/3/2025",
        "1001",
        1.1,
        "Octanoic acid, pentadecafluoro-, anhydride",
        72,
        "x",
        1,
        "y",
        1,
        "old comments",
    ]
    wb = tmp_path / "dup_headers.xlsx"
    with pd.ExcelWriter(wb) as xw:
        pd.DataFrame([old_header, old_row]).to_excel(
            xw, sheet_name="Old", index=False, header=False
        )

    classes_yaml = tmp_path / "classes.yaml"
    classes_yaml.write_text("version: '1'\nmap: {}\n", encoding="utf-8")

    code = run_pipeline(wb, classes_yaml, tmp_path / "runs")
    assert code != 0
    # On failure, standardized_*.xlsx should not be produced
    outs = list((tmp_path / "runs").glob("*/standardized_*.xlsx"))
    assert not outs
