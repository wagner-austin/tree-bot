from __future__ import annotations

import pandas as pd


def trim_cartridge(df: pd.DataFrame) -> pd.DataFrame:
    """Remove leading/trailing whitespace from CartridgeNum column."""
    df2 = df.copy()
    df2["CartridgeNum"] = df2["CartridgeNum"].astype(str).str.strip()
    return df2
