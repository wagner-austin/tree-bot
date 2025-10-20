from __future__ import annotations

import pandas as pd

from treebot.services.transform_service import transform_old_to_new


def test_canonicalization_applied() -> None:
    df_old = pd.DataFrame(
        [
            {
                "DataFolderName": "DF",
                "DateRun": "4/3/2025",
                "CartridgeNum": "1",
                "RetentionTime": 1.0,
                "Match1": "1,3-butadiene, 2-methyl",
                "Match1.Quality": 50,
                "Match2": "x",
                "Match2.Quality": 1,
                "Match3": "y",
                "Match3.Quality": 1,
                "Comments": "",
            }
        ]
    )
    class_map = {"isoprene": "Terpene"}
    canon_map = {"1,3-butadiene, 2-methyl": "isoprene"}

    res = transform_old_to_new(df_old, class_map, canon_map)
    assert res.df.loc[0, "Compound"] == "isoprene"
    assert res.df.loc[0, "Class"] == "Terpene"
