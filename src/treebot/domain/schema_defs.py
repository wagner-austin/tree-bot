from __future__ import annotations

from typing import List

OLD_COMMENTS_HEADER = "Comments (note here, for example, if there are common names and official IUPAC names that are actually the same compound)"

REQUIRED_OLD: List[str] = [
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
    OLD_COMMENTS_HEADER,
]

REQUIRED_NEW: List[str] = [
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

OUTPUT_ORDER: List[str] = REQUIRED_NEW.copy()
