from __future__ import annotations

from pathlib import Path

import pandas as pd

from treebot.services.aggregate.summary import build_summary
from treebot.services.output.summary_writer import write_sections_to_sheet


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

    sections = build_summary(
        per_sheet, quality_min=80, quality_max=None, count_min=1, count_max=None
    )
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

    sec = Section(
        site="EmersonOaks",
        species="artcal",
        df=df_section,
        stats={
            "unique_compounds": 0,
            "total_peaks": 0,
            "unique_compounds_all": 0,
            "peaks_all": 0,
        },
    )
    write_sections_to_sheet(std_path, [sec], "Summary")

    # Read back Summary sheet to verify content
    # The first row is a text header for the section; actual table header is on the next row
    back = pd.read_excel(std_path, sheet_name="Summary", header=1)
    assert "Compound" in back.columns
    assert "Compound Class" in back.columns
    # Ensure the row was written
    assert (back["Compound"] == "isoprene").any()


def test_write_multi_sheets_unique_table_names(tmp_path: Path) -> None:
    # Prepare standardized workbook
    std_path = tmp_path / "standardized_test.xlsx"
    pd.DataFrame({"A": [1]}).to_excel(std_path, index=False, sheet_name="Sheet1")

    # Single section that will be written to two different sheets
    df_section = pd.DataFrame(
        [
            {
                "Compound": "isoprene",
                "Compound Class": "terpene",
                "RetentionMin": 2.05,
                "RetentionMax": 2.07,
                "RtRange": 0.02,
                "AvgMatchQuality": 87.5,
                "Count": 1,
                "Comments": "solid match",
            }
        ]
    )
    from treebot.services.aggregate.summary import Section

    sec = Section(
        site="EmersonOaks",
        species="artcal",
        df=df_section,
        stats={
            "unique_compounds": 0,
            "total_peaks": 0,
            "unique_compounds_all": 0,
            "peaks_all": 0,
        },
    )

    # Write to two summary sheets; should not raise due to table name collision
    write_sections_to_sheet(std_path, [sec], "Summary")
    write_sections_to_sheet(std_path, [sec], "HQ Single")

    # Verify both sheets have content
    back_summary = pd.read_excel(std_path, sheet_name="Summary", header=1)
    back_hq = pd.read_excel(std_path, sheet_name="HQ Single", header=1)
    assert (back_summary["Compound"] == "isoprene").any()
    assert (back_hq["Compound"] == "isoprene").any()

    # Inspect table names via openpyxl and ensure uniqueness across workbook
    from openpyxl import load_workbook

    wb = load_workbook(std_path)
    table_names = set()
    for ws in wb.worksheets:
        for t in ws._tables.values():  # openpyxl Table objects
            assert t.displayName not in table_names
            table_names.add(t.displayName)


def test_build_summary_routing_by_quality_and_count() -> None:
    # Compose per-sheet data with compounds spanning HQ/LQ and single/multiple occurrences
    df = pd.DataFrame(
        [
            # HQ single (>=80, count 1)
            {
                "Sheet": "SiteA",
                "Species": "sp1",
                "RetentionTime": 1.0,
                "Compound": "A",
                "Class": "cls",
                "MatchScore": 90,
                "Comments": "",
            },
            # LQ single (<80, count 1)
            {
                "Sheet": "SiteA",
                "Species": "sp1",
                "RetentionTime": 2.0,
                "Compound": "B",
                "Class": "cls",
                "MatchScore": 70,
                "Comments": "",
            },
            # LQ multiple (<80, count 2)
            {
                "Sheet": "SiteA",
                "Species": "sp1",
                "RetentionTime": 3.0,
                "Compound": "C",
                "Class": "cls",
                "MatchScore": 75,
                "Comments": "",
            },
            {
                "Sheet": "SiteA",
                "Species": "sp1",
                "RetentionTime": 3.1,
                "Compound": "C",
                "Class": "cls",
                "MatchScore": 78,
                "Comments": "",
            },
            # Blank species should be skipped
            {
                "Sheet": "SiteA",
                "Species": "",
                "RetentionTime": 4.0,
                "Compound": "D",
                "Class": "cls",
                "MatchScore": 90,
                "Comments": "",
            },
        ]
    )
    per_sheet = {"SiteA": df}

    # Config threshold
    q = 80

    # HQ Single: quality >= q, count == 1
    from treebot.services.aggregate.summary import build_summary

    hq_single = build_summary(per_sheet, quality_min=q, quality_max=None, count_min=1, count_max=1)
    assert len(hq_single) == 1
    assert "A" in set(hq_single[0].df["Compound"])  # HQ single compound present
    assert "B" not in set(hq_single[0].df["Compound"])  # LQ
    assert "C" not in set(hq_single[0].df["Compound"])  # count 2

    # LQ Single: 0 <= quality <= q-1, count == 1
    lq_single = build_summary(per_sheet, quality_min=0, quality_max=q - 1, count_min=1, count_max=1)
    assert len(lq_single) == 1
    assert "B" in set(lq_single[0].df["Compound"])  # LQ single compound present
    assert "C" not in set(lq_single[0].df["Compound"])  # count 2

    # LQ Multiple: 0 <= quality <= q-1, count >= 2
    lq_multiple = build_summary(
        per_sheet, quality_min=0, quality_max=q - 1, count_min=2, count_max=None
    )
    assert len(lq_multiple) == 1
    assert set(lq_multiple[0].df["Compound"]) == {"C"}
