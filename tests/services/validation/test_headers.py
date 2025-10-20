from __future__ import annotations

from pathlib import Path

import pandas as pd

from treebot.services.validation.headers import normalize_headers
from treebot.services.io_excel import write_excel


def test_normalize_headers_renames_old_comments() -> None:
    old_header = "Comments (note here, for example, if there are common names and official IUPAC names that are actually the same compound)"
    df = pd.DataFrame(columns=["A", old_header])
    df2 = normalize_headers(df, "old")
    assert "Comments" in df2.columns


def test_write_excel_adds_missing_new_schema_columns(tmp_path: Path) -> None:
    # Minimal df missing many columns; write_excel should add new schema columns
    df = pd.DataFrame({"DateRun": []})
    out = tmp_path / "o.xlsx"
    write_excel({"Sheet1": df}, out)
    assert out.exists()
    df_back = pd.read_excel(out, sheet_name="Sheet1")
    # Spot-check key new schema columns exist
    for col in ["Species", "Compound", "Class", "MatchScore"]:
        assert col in df_back.columns
