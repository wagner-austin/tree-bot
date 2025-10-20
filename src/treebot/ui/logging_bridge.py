from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List


@dataclass
class UiLogBuffer:
    max_lines: int = 200
    lines: List[str] = field(default_factory=list)

    def append(self, text: str) -> None:
        self.lines.append(text)
        if len(self.lines) > self.max_lines:
            # keep only the last max_lines
            self.lines[:] = self.lines[-self.max_lines :]

    def dump(self) -> str:
        return "\n".join(self.lines)


class UiLogHandler(logging.Handler):
    def __init__(self, buffer: UiLogBuffer) -> None:
        super().__init__()
        self.buffer = buffer

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self.buffer.append(msg)
        except Exception:  # pragma: no cover - defensive
            pass


def attach_ui_log_handler(logger: logging.Logger, level: int = logging.INFO) -> UiLogBuffer:
    buf = UiLogBuffer()
    handler = UiLogHandler(buf)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    logger.addHandler(handler)
    return buf
