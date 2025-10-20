from __future__ import annotations

import logging

from treebot.ui.logging_bridge import UiLogBuffer, attach_ui_log_handler


def test_logging_bridge_appends_and_truncates() -> None:
    buf = UiLogBuffer(max_lines=3)
    for i in range(5):
        buf.append(f"line {i}")
    dumped = buf.dump().splitlines()
    assert dumped == ["line 2", "line 3", "line 4"]


def test_attach_ui_log_handler_captures_logs() -> None:
    logger = logging.getLogger("treebot.test.ui")
    logger.setLevel(logging.INFO)
    buf = attach_ui_log_handler(logger)
    logger.info("hello")
    assert "hello" in buf.dump()
