from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Optional


class ErrorCategory(str, Enum):
    SCHEMA_ERROR = "SCHEMA_ERROR"
    MAPPING_MISSING = "MAPPING_MISSING"
    DUPLICATE_KEY = "DUPLICATE_KEY"


@dataclass(frozen=True)
class ValidationIssue:
    category: ErrorCategory
    code: str
    message: str
    row_index: Optional[int] = None
    details: Optional[Mapping[str, object]] = None
