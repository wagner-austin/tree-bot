from __future__ import annotations

import pandas as pd

from treebot.services.transform_service import transform_old_to_new


def test_transform_maps_species_and_class() -> None:
    df_old = pd.DataFrame(
        [
            {
                "DataFolderName": "DF1",
                "DateRun": "4/3/2025",
                "CartridgeNum": "1",
                "RetentionTime": 1.0,
                "Match1": "Octanoic acid, pentadecafluoro-, anhydride",
                "Match1.Quality": 72,
                "Match2": "x",
                "Match2.Quality": 1,
                "Match3": "y",
                "Match3.Quality": 1,
                "Comments": "",
            }
        ]
    )
    class_map = {"octanoic acid, pentadecafluoro-, anhydride": "PFAS"}

    res = transform_old_to_new(df_old, class_map)
    assert not res.issues
    # Species is now empty (NA) since we removed mapping file support
    assert pd.isna(res.df.loc[0, "Species"])
    assert res.df.loc[0, "Class"] == "PFAS"
    assert res.df.loc[0, "MatchScore"] == 72


def test_transform_unmapped_class_records_issue() -> None:
    df_old = pd.DataFrame(
        [
            {
                "DataFolderName": "DF1",
                "DateRun": "4/3/2025",
                "CartridgeNum": "1",
                "RetentionTime": 1.0,
                "Match1": "Unknown Compound",
                "Match1.Quality": 50,
                "Match2": "x",
                "Match2.Quality": 1,
                "Match3": "y",
                "Match3.Quality": 1,
                "Comments": "",
            }
        ]
    )
    class_map: dict[str, str] = {}

    res = transform_old_to_new(df_old, class_map)
    assert any(i.code == "CLASS_MISSING" for i in res.issues)
    assert not res.unmapped_compounds.empty
