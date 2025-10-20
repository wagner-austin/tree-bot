from __future__ import annotations

import logging

from treebot.utils.logging_setup import ExtraAwareFormatter


def test_extra_aware_formatter_keeps_message_clean() -> None:
    rec = logging.LogRecord(
        name="treebot.main",
        level=logging.ERROR,
        pathname=__file__,
        lineno=1,
        msg="Run FAILED with blocking issues",
        args=(),
        exc_info=None,
    )
    fmt = ExtraAwareFormatter("%(levelname)s | %(name)s | %(message)s")
    out = fmt.format(rec)
    # Extras are not appended; message remains clean and may contain newlines
    assert out.startswith("ERROR | treebot.main | Run FAILED")
