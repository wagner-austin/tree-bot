from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path
from typing import BinaryIO


def open_path(path: Path) -> None:
    """Open a file or directory in the OS default handler, cross-platform.

    - Windows: uses os.startfile when available
    - macOS: uses 'open'
    - Linux/other: uses 'xdg-open' if available
    """
    try:
        if sys.platform.startswith("win"):
            startfile = getattr(os, "startfile", None)
            if callable(startfile):
                startfile(str(path))
                return
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=False)
            return
        # Fallback for Linux/others
        subprocess.run(["xdg-open", str(path)], check=False)
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
