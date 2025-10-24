from __future__ import annotations

from pathlib import Path

import pandas as pd

from treebot.main import run_pipeline


def test_multisheet_mixed_schemas(tmp_path: Path) -> None:
    old_header = [
        "DataFolderName",
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
    new_header = [
        "DataFolderName",
        "DateRun",
        "CartridgeNum",
        "Species",
        "RetentionTime",
        "Match1",
        "Match1.Quality",
        "Match2",
        "Match2.Quality",
        "Match3",
        "Match3.Quality",
        "Comments",
        "Compound",
        "Class",
        "MatchScore",
    ]
    new_row = [
        "DF2",
        "4/3/2025",
        "1002",
        "artcal",
        1.5,
        "1,3-butadiene, 2-methyl",
        60,
        "x",
        1,
        "y",
        1,
        "new comments",
        "1,3-butadiene, 2-methyl",
        "Terpene",
        60,
    ]

    results_xlsx = tmp_path / "mixed.xlsx"
    with pd.ExcelWriter(results_xlsx) as xw:
        pd.DataFrame([["intro"], ["data below"], old_header, old_row]).to_excel(
            xw, sheet_name="Old1", index=False, header=False
        )
        pd.DataFrame([new_row], columns=new_header).to_excel(xw, sheet_name="New1", index=False)
        pd.DataFrame([["notes"], ["not a table"]]).to_excel(
            xw, sheet_name="Notes", index=False, header=False
        )

    mapping_xlsx = tmp_path / "mapping.xlsx"
    pd.DataFrame(
        [["4/3/2025", "1001", "artcal"]], columns=["DateRun", "CartridgeNum", "Species"]
    ).to_excel(mapping_xlsx, index=False)

    classes_yaml = tmp_path / "classes.yaml"
    classes_yaml.write_text(
        """
version: "1"
map:
  "octanoic acid, pentadecafluoro-, anhydride": "PFAS"
  "1,3-butadiene, 2-methyl": "Terpene"
        """.strip(),
        encoding="utf-8",
    )

    code = run_pipeline(results_xlsx, classes_yaml, tmp_path / "runs")
    assert code == 0
    outs = list((tmp_path / "runs").glob("*/standardized_*.xlsx"))
    assert outs, "standardized.xlsx missing"

    # Read data sheets only (exclude summary sheets)
    xl = pd.ExcelFile(outs[0])
    # Exclude all summary sheets written by the orchestrator
    summary_sheets = {"HQ Multiple", "HQ Single", "Lq Multiple", "Lq Single", "Summary"}
    data_sheet_names = [name for name in xl.sheet_names if name not in summary_sheets]
    all_sheets = [pd.read_excel(outs[0], sheet_name=name) for name in data_sheet_names]
    df_out = pd.concat(all_sheets, ignore_index=True)

    assert len(df_out) == 2
    assert set(df_out["CartridgeNum"].astype(str)) == {"1001", "1002"}
