from __future__ import annotations

from pathlib import Path

import pandas as pd

from treebot.main import run_pipeline


def write_excel(df: pd.DataFrame, path: Path) -> None:
    df.to_excel(path, index=False)


def test_old_to_new_success(tmp_path: Path) -> None:
    old = pd.DataFrame(
        [
            {
                "DataFolderName": "DF1",
                "DateRun": "4/3/2025",
                "CartridgeNum": "0001",
                "RetentionTime": 1.23,
                "Match1": "Octanoic acid, pentadecafluoro-, anhydride",
                "Match1.Quality": 72,
                "Match2": "x",
                "Match2.Quality": 10,
                "Match3": "y",
                "Match3.Quality": 5,
                "Comments (note here, for example, if there are common names and official IUPAC names that are actually the same compound)": " test ",
            }
        ]
    )
    results_xlsx = tmp_path / "results_old.xlsx"
    write_excel(old, results_xlsx)

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

    code = run_pipeline(results_xlsx, classes_yaml, tmp_path / "runs")
    assert code == 0
    outs = list((tmp_path / "runs").glob("*/standardized_*.xlsx"))
    assert outs, "standardized.xlsx missing"
    df_out = pd.read_excel(outs[0])
    # Species is now empty (NA) since we removed mapping file support
    assert pd.isna(df_out.loc[0, "Species"])
    assert df_out.loc[0, "Class"] == "PFAS"
    assert df_out.loc[0, "MatchScore"] == 72
    assert df_out.loc[0, "DateRun"] == "2025-04-03"


def test_new_schema_mismatch_no_validation(tmp_path: Path) -> None:
    new = pd.DataFrame(
        [
            {
                "DataFolderName": "DF1",
                "DateRun": "4/3/2025",
                "CartridgeNum": "0001",
                "Species": "artcal",
                "RetentionTime": 1.23,
                "Match1": "1, 3-butadiene, 2-methyl",
                "Match1.Quality": 60,
                "Match2": "x",
                "Match2.Quality": 10,
                "Match3": "y",
                "Match3.Quality": 5,
                "Comments": "",
                "Compound": "1,3-butadiene, 2-methyl",
                "Class": "WrongClass",
                "MatchScore": 60,
            }
        ]
    )
    results_xlsx = tmp_path / "results_new.xlsx"
    write_excel(new, results_xlsx)

    classes_yaml = tmp_path / "classes.yaml"
    classes_yaml.write_text(
        """
version: "1"
map:
  "1,3-butadiene, 2-methyl": "Terpene"
        """.strip(),
        encoding="utf-8",
    )

    code = run_pipeline(results_xlsx, classes_yaml, tmp_path / "runs")
    # New schema rows are passed through without class/matchscore validation in the MVP
    assert code == 0
    outs = list((tmp_path / "runs").glob("*/standardized_*.xlsx"))
    assert outs
