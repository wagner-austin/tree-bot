from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import List, Mapping, Optional

import pandas as pd

from ..domain.errors import ValidationIssue
from .transform.old_to_new import old_to_new as _old_to_new


@dataclass(frozen=True)
class TransformResult:
    df: pd.DataFrame
    issues: List[ValidationIssue]
    unmapped_compounds: pd.DataFrame


def transform_old_to_new(
    df_old: pd.DataFrame,
    class_map: Mapping[str, str],
    canon_map: Optional[Mapping[str, str]] = None,
) -> TransformResult:
    final, issues, unmapped = _old_to_new(df_old, class_map, canon_map)
    return TransformResult(df=final, issues=issues, unmapped_compounds=unmapped)


class TransformService:
    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger

    def old_to_new(
        self,
        df_old: pd.DataFrame,
        class_map: Mapping[str, str],
        canon_map: Optional[Mapping[str, str]] = None,
    ) -> TransformResult:
        self.logger.info("Transforming old->new", extra={"rows": len(df_old)})
        return transform_old_to_new(df_old, class_map, canon_map)
