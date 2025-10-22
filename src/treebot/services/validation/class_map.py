from __future__ import annotations

from pathlib import Path
from typing import Dict

import yaml

from ...utils.normalize import normalize_compound_name


def load_class_map(path: Path) -> Dict[str, str]:
    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    mapping: Dict[str, str] = {}
    mp = raw.get("map", {}) if isinstance(raw, dict) else {}
    for k, v in mp.items():
        if not isinstance(k, str) or not isinstance(v, str):
            continue
        mapping[normalize_compound_name(k)] = v
    return mapping
