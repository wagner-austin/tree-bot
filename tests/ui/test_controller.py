from __future__ import annotations

from pathlib import Path

import pandas as pd

from treebot.ui.controller import UiController
from treebot.config import Config


def write_excel(df: pd.DataFrame, path: Path) -> None:
    df.to_excel(path, index=False)


def test_ui_controller_run_success(tmp_path: Path) -> None:
    # Minimal old schema row
    old = pd.DataFrame(
        [
            {
                "DataFolderName": "DF1",
                "DateRun": "4/3/2025",
                "CartridgeNum": "1",
                "RetentionTime": 1.0,
                "Match1": "Octanoic acid, pentadecafluoro-, anhydride",
                "Match1.Quality": 72,
                "Match2": "x",
                "Match2.Quality": 10,
                "Match3": "y",
                "Match3.Quality": 5,
                "Comments (note here, for example, if there are common names and official IUPAC names that are actually the same compound)": "",
            }
        ]
    )
    results = tmp_path / "results.xlsx"
    write_excel(old, results)

    mapping = pd.DataFrame([{"DateRun": "4/3/2025", "CartridgeNum": "1", "Species": "artcal"}])
    mapping_xlsx = tmp_path / "mapping.xlsx"
    write_excel(mapping, mapping_xlsx)

    classes_yaml = tmp_path / "classes.yaml"
    classes_yaml.write_text(
        """
version: "1"
map:
  "octanoic acid, pentadecafluoro-, anhydride": "PFAS"
        """.strip(),
        encoding="utf-8",
    )

    ctrl = UiController()
    res = ctrl.run(results, classes_yaml, tmp_path / "runs", Config())
    assert res.code == 0
    assert res.run_dir is not None
