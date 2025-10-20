from __future__ import annotations

from treebot.ui.app import _cleanup_logging


def test_cleanup_logging_no_exceptions() -> None:
    # Should be safe to call multiple times and not raise
    _cleanup_logging()
    _cleanup_logging()
