from __future__ import annotations

from pathlib import Path

import pandas as pd

from treebot.services.io_excel import read_results_workbook


def test_read_results_workbook_recovers_tables(tmp_path: Path) -> None:
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
    old_row = ["DF1", "4/3/2025", "1001", 1.1, "Hexane", 10, "x", 1, "y", 1, "c"]

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
        "Hexane",
        10,
        "x",
        1,
        "y",
        1,
        "",
        "Hexane",
        "Hydrocarbon",
        10,
    ]

    wb = tmp_path / "wb.xlsx"
    with pd.ExcelWriter(wb) as xw:
        pd.DataFrame([["junk"], ["ignore"], old_header, old_row]).to_excel(
            xw, sheet_name="Old", index=False, header=False
        )
        pd.DataFrame([new_row], columns=new_header).to_excel(xw, sheet_name="New", index=False)
        pd.DataFrame([["notes"], ["no data"]]).to_excel(
            xw, sheet_name="Notes", index=False, header=False
        )

    sheets = read_results_workbook(wb)
    names = [s.name for s in sheets]
    assert "Old" in names and "New" in names
    schema_map = {s.name: s.schema for s in sheets}
    assert schema_map["Old"] == "old"
    assert schema_map["New"] == "new"
