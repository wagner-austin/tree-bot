from __future__ import annotations

import pandas as pd

from treebot.services.io_excel import detect_schema


def test_detect_old_schema() -> None:
    df = pd.DataFrame(
        columns=[
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
    )
    assert detect_schema(df) == "old"


def test_detect_new_schema() -> None:
    df = pd.DataFrame(
        columns=[
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
    )
    assert detect_schema(df) == "new"
