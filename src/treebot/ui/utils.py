from __future__ import annotations

import os
from pathlib import Path
from typing import BinaryIO


def open_path(path: Path) -> None:
    try:
        os.startfile(str(path))  # Windows-only
    except Exception:
        # Best-effort; UI shows clear links regardless
        pass


def save_uploaded_file(dest_dir: Path, name: str, content: bytes | BinaryIO) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / name
    if hasattr(content, "read"):
        data = content.read()
    else:
        data = content
    with open(dest, "wb") as f:
        f.write(data)
    return dest
