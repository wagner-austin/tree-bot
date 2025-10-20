from __future__ import annotations

import pandas as pd

from treebot.services.validation.dates import parse_dates_to_iso


def test_parse_dates_to_iso_valid() -> None:
    df = pd.DataFrame({"DateRun": ["4/3/2025", "12/25/2020"]})
    df2, issues = parse_dates_to_iso(df)
    assert not issues
    assert df2.loc[0, "DateRun"] == "2025-04-03"
    assert df2.loc[1, "DateRun"] == "2020-12-25"
