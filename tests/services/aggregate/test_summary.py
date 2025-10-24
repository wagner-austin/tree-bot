from __future__ import annotations

from pathlib import Path

import pandas as pd

from treebot.services.aggregate.summary import build_summary
from treebot.services.output.summary_writer import write_summary_into_workbook


def test_build_summary_basic(tmp_path: Path) -> None:
    # Prepare a minimal per-sheet input
    df = pd.DataFrame(
        [
            {
                "Sheet": "EmersonOaks",
                "Species": "artcal",
                "RetentionTime": 2.05,
                "Compound": "isoprene",
                "Class": "terpene",
                "MatchScore": 85,
                "Comments": "solid match",
            },
            {
                "Sheet": "EmersonOaks",
                "Species": "artcal",
                "RetentionTime": 2.07,
                "Compound": "isoprene",
                "Class": "terpene",
                "MatchScore": 90,
                "Comments": "",
            },
            {
                "Sheet": "EmersonOaks",
                "Species": "artcal",
                "RetentionTime": 4.86,
                "Compound": "benzene",
                "Class": "aromatic",
                "MatchScore": 75,  # filtered out by threshold
                "Comments": "below threshold",
            },
            {
                "Sheet": "EmersonOaks",
                "Species": "",  # blank species should be skipped entirely
                "RetentionTime": 3.00,
                "Compound": "toluene",
                "Class": "aromatic",
                "MatchScore": 95,
                "Comments": "",
            },
        ]
    )
    per_sheet = {"EmersonOaks": df}

    sections = build_summary(per_sheet, quality_threshold=80, min_count=1)
    # Only one section: Species 'artcal'
    assert len(sections) == 1
    sec = sections[0]
    assert sec.site == "EmersonOaks"
    assert sec.species == "artcal"

    # Stats reflect kept rows (2 peaks for isoprene)
    assert sec.stats.get("total_peaks") == 2
    assert sec.stats.get("unique_compounds") == 1

    # Columns and values
    cols = list(sec.df.columns)
    assert cols == [
        "Compound",
        "Compound Class",
        "RetentionMin",
        "RetentionMax",
        "RtRange",
        "AvgMatchQuality",
        "Count",
        "Comments",
    ]
    assert sec.df.iloc[0]["Compound"] == "isoprene"
    assert sec.df.iloc[0]["Compound Class"] == "terpene"
    assert sec.df.iloc[0]["Count"] == 2
    assert sec.df.iloc[0]["AvgMatchQuality"] == 87.5  # (85 + 90) / 2
    # Carries forward the first non-empty comment
    assert sec.df.iloc[0]["Comments"] == "solid match"


def test_write_summary_into_workbook(tmp_path: Path) -> None:
    # Create a minimal standardized workbook to append Summary into
    std_path = tmp_path / "standardized_test.xlsx"
    base = pd.DataFrame({"A": [1]})
    base.to_excel(std_path, index=False, sheet_name="Sheet1")

    # Make one section
    df_section = pd.DataFrame(
        [
            {
                "Compound": "isoprene",
                "Compound Class": "terpene",
                "RetentionMin": 2.05,
                "RetentionMax": 2.07,
                "RtRange": 0.02,
                "AvgMatchQuality": 87.5,
                "Count": 2,
                "Comments": "solid match",
            }
        ]
    )

    from treebot.services.aggregate.summary import Section

    sec = Section(site="EmersonOaks", species="artcal", df=df_section, stats={})
    write_summary_into_workbook(std_path, [sec])

    # Read back Summary sheet to verify content
    # The first row is a text header for the section; actual table header is on the next row
    back = pd.read_excel(std_path, sheet_name="Summary", header=1)
    assert "Compound" in back.columns
    assert "Compound Class" in back.columns
    # Ensure the row was written
    assert (back["Compound"] == "isoprene").any()
