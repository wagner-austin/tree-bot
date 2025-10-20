from __future__ import annotations

import json
import logging
from dataclasses import dataclass
import sys
from pathlib import Path
from typing import Any, Dict


@dataclass(frozen=True)
class LogFiles:
    human: Path
    jsonl: Path


class JsonLineFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "time": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S"),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        # Extra attributes
        for key, value in record.__dict__.items():
            if key not in (
                "args",
                "asctime",
                "created",
                "exc_info",
                "exc_text",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "msg",
                "name",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "thread",
                "threadName",
            ):
                payload[key] = value
        return json.dumps(payload, ensure_ascii=False)


class ExtraAwareFormatter(logging.Formatter):
    SAFE_KEYS = {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
    }

    def format(self, record: logging.LogRecord) -> str:
        # Keep console output clean and human-friendly; message may include newlines
        return super().format(record)


def setup_logging(run_dir: Path) -> LogFiles:
    run_dir.mkdir(parents=True, exist_ok=True)
    human_log = run_dir / "latest_run.log"
    jsonl_log = run_dir / "logs.jsonl"

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Clear existing handlers for repeatable runs
    for h in list(logger.handlers):
        logger.removeHandler(h)

    human_handler = logging.FileHandler(human_log, encoding="utf-8")
    human_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    )
    human_handler.setLevel(logging.INFO)

    json_handler = logging.FileHandler(jsonl_log, encoding="utf-8")
    json_handler.setFormatter(JsonLineFormatter())
    json_handler.setLevel(logging.INFO)

    logger.addHandler(human_handler)
    logger.addHandler(json_handler)

    # Also log to console for immediate visibility; prefer Rich if available
    try:
        from rich.logging import RichHandler

        rich_handler = RichHandler(
            level=logging.INFO,
            markup=True,
            show_time=True,
            show_path=False,
            rich_tracebacks=True,
            log_time_format="%Y-%m-%d %H:%M:%S",
        )
        # Base message only; RichHandler shows time/level
        rich_handler.setFormatter(ExtraAwareFormatter("%(message)s"))
        logger.addHandler(rich_handler)
    except Exception:
        console = logging.StreamHandler(stream=sys.stdout)
        console.setFormatter(
            ExtraAwareFormatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        )
        console.setLevel(logging.INFO)
        logger.addHandler(console)

    return LogFiles(human=human_log, jsonl=jsonl_log)
