from __future__ import annotations

from pathlib import Path


def default_output_base() -> Path:
    # Use a workspace-local runs directory instead of user Downloads
    # This keeps artifacts beside the project and avoids permission quirks.
    return Path.cwd() / "runs"


def default_uploads_dir() -> Path:
    return Path.home() / "Downloads" / "TreeBotUploads"
