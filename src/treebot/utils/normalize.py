from __future__ import annotations

import re
import unicodedata
from typing import Final


_GREEK_MAP: Final[dict[str, str]] = {
    "α": "alpha",
    "β": "beta",
    "γ": "gamma",
    "δ": "delta",
    "ε": "epsilon",
    "μ": "mu",
    "π": "pi",
}


def _fold_greek(text: str) -> str:
    for k, v in _GREEK_MAP.items():
        text = text.replace(k, v)
    return text


def normalize_text(value: str) -> str:
    """Deterministic normalization used for keys and mapping.

    Steps:
    - lowercase
    - trim ends
    - collapse internal whitespace
    - unify comma/hyphen spacing
    - strip trailing punctuation/hyphens
    - unicode fold (e.g., greek letters)
    """
    s = value
    s = unicodedata.normalize("NFKC", s)
    s = _fold_greek(s)
    s = s.lower()
    s = s.strip()
    # Collapse internal whitespace
    s = re.sub(r"\s+", " ", s)
    # Normalize spaces around commas and hyphens
    s = re.sub(r"\s*,\s*", ", ", s)
    s = re.sub(r"\s*-\s*", "-", s)
    # Strip trailing punctuation/hyphens
    s = re.sub(r"[\s\-\.,;:]+$", "", s)
    return s
