from __future__ import annotations

from pathlib import Path
from typing import Dict

import yaml

from ...utils.normalize import normalize_text


def load_name_canon(path: Path) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    if not path.exists():
        return mapping
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return mapping
    mp = raw.get("map", {})
    if not isinstance(mp, dict):
        return mapping
    for k, v in mp.items():
        if isinstance(k, str) and isinstance(v, str):
            mapping[normalize_text(k)] = normalize_text(v)
    return mapping
