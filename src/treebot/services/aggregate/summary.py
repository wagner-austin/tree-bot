from __future__ import annotations

from dataclasses import dataclass
from typing import List, Mapping

import pandas as pd
from ...types import SectionStats


@dataclass(frozen=True)
class Section:
    site: str
    species: str
    df: pd.DataFrame
    stats: SectionStats


@dataclass(frozen=True)
class SheetConfig:
    """Configuration for a summary output sheet."""

    name: str
    quality_min: int
    quality_max: int | None
    count_min: int
    count_max: int | None


def _safe_numeric(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def _first_class_or_mixed(classes: pd.Series) -> str | None:
    vals = [str(x) for x in classes.dropna().astype(str).tolist() if str(x).strip()]
    if not vals:
        return None
    uniq = sorted(set(vals))
    if len(uniq) == 1:
        return uniq[0]
    return "mixed"


def build_summary(
    per_sheet: Mapping[str, pd.DataFrame],
    quality_min: int,
    quality_max: int | None,
    count_min: int,
    count_max: int | None,
) -> List[Section]:
    """Build per (Site > Species) compound summary sections with flexible filtering.

    Input DataFrames must contain at least: Sheet, Species, RetentionTime,
    Compound, Class, MatchScore.

    Args:
        per_sheet: Dict of sheet name to DataFrame
        quality_min: Minimum MatchScore (inclusive)
        quality_max: Maximum MatchScore (inclusive), None = no upper limit
        count_min: Minimum compound count (inclusive)
        count_max: Maximum compound count (inclusive), None = no upper limit
    """
    sections: List[Section] = []

    # Stable site order by key (sheet name)
    for site, df in per_sheet.items():
        if df.empty:
            continue
        # Ensure expected columns exist
        cols = set(df.columns.astype(str))
        required = {"Species", "RetentionTime", "Compound", "Class", "MatchScore"}
        if not required.issubset(cols):
            # Skip sheets lacking required fields
            continue

        # Filter by quality range and presence of Compound
        tmp = df.copy()
        tmp["MatchScore"] = _safe_numeric(tmp["MatchScore"])  # pandas column access
        tmp = tmp[tmp["MatchScore"].fillna(-1) >= quality_min]
        if quality_max is not None:
            tmp = tmp[tmp["MatchScore"].fillna(-1) <= quality_max]
        tmp = tmp[tmp["Compound"].astype(str).str.strip() != ""]
        if tmp.empty:
            continue

        # Group by Species then aggregate by Compound within species
        for species, sub in tmp.groupby("Species", dropna=False):
            # Skip groups with missing/blank species
            sp = "" if pd.isna(species) else str(species).strip()
            if not sp:
                continue
            if sub.empty:
                continue

            # Aggregate by Compound
            @dataclass(frozen=True)
            class SummaryRow:
                Compound: str
                _Compound_Class: str | None
                RetentionMin: float
                RetentionMax: float
                RtRange: float
                AvgMatchQuality: float
                Count: int
                Comments: str

            rows: List[SummaryRow] = []
            # Pre-filter stats (before min_count)
            unique_compounds_all = int(
                sub["Compound"].astype(str).str.strip().replace("", pd.NA).dropna().nunique()
            )
            peaks_all = int(len(sub))
            for comp, g in sub.groupby("Compound"):
                s_rt = _safe_numeric(g["RetentionTime"])  # pandas column access
                rt_min = float(s_rt.min()) if not s_rt.dropna().empty else float("nan")
                rt_max = float(s_rt.max()) if not s_rt.dropna().empty else float("nan")
                rt_range = (
                    rt_max - rt_min if (pd.notna(rt_min) and pd.notna(rt_max)) else float("nan")
                )
                cls = _first_class_or_mixed(g["Class"])  # pandas column access
                # Calculate average MatchScore
                s_ms = _safe_numeric(g["MatchScore"])
                avg_match_quality = float(s_ms.mean()) if not s_ms.dropna().empty else float("nan")
                # Carry forward the first non-empty comment if any
                comment_val: str = ""
                if "Comments" in g.columns:
                    for v in g["Comments"].astype(str).tolist():
                        vv = v.strip()
                        if vv and vv.lower() != "nan":
                            comment_val = vv
                            break
                rows.append(
                    SummaryRow(
                        Compound=str(comp),
                        _Compound_Class=cls,
                        RetentionMin=rt_min,
                        RetentionMax=rt_max,
                        RtRange=round(rt_range, 3) if pd.notna(rt_range) else rt_range,
                        AvgMatchQuality=(
                            round(avg_match_quality, 1)
                            if pd.notna(avg_match_quality)
                            else avg_match_quality
                        ),
                        Count=int(len(g)),
                        Comments=comment_val,
                    )
                )

            if not rows:
                continue

            # Convert dataclass rows to DataFrame with desired column names
            out = pd.DataFrame(
                [
                    {
                        "Compound": r.Compound,
                        "Compound Class": r._Compound_Class,
                        "RetentionMin": r.RetentionMin,
                        "RetentionMax": r.RetentionMax,
                        "RtRange": r.RtRange,
                        "AvgMatchQuality": r.AvgMatchQuality,
                        "Count": r.Count,
                        "Comments": r.Comments,
                    }
                    for r in rows
                ]
            )
            # Frequency filter by range and sorting
            out = out[out["Count"] >= int(count_min)]
            if count_max is not None:
                out = out[out["Count"] <= int(count_max)]
            if out.empty:
                continue
            out = out.sort_values(["Count", "Compound"], ascending=[False, True], kind="mergesort")

            # Post-filter stats (kept rows)
            unique_compounds_kept = int(out["Compound"].nunique())
            peaks_kept = int(out["Count"].sum())

            stats: SectionStats = {
                "unique_compounds": unique_compounds_kept,  # kept
                "total_peaks": peaks_kept,  # kept
                "unique_compounds_all": unique_compounds_all,
                "peaks_all": peaks_all,
            }
            sections.append(Section(site=site, species=sp, df=out, stats=stats))

    return sections
