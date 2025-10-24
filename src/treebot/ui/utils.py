from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path
from typing import BinaryIO


def open_path(path: Path) -> None:
    """Open a path via the OS default handler and try to bring it to front on click.

    - Windows: prefer `cmd /c start "" <path>` which reliably focuses Explorer.
    - macOS: `open <path>` (Finder comes to front).
    - Linux: `xdg-open <path>` (focus behavior depends on DE).
    """
    try:
        if sys.platform.startswith("win"):
            # Use `start` via cmd to better foreground the window.
            try:
                subprocess.run(["cmd", "/c", "start", "", str(path)], check=False)
            except Exception:
                # Fallback to os.startfile if available
                startfile = getattr(os, "startfile", None)
                if callable(startfile):
                    startfile(str(path))
            return
        if sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=False)
            return
        # Linux/others
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
