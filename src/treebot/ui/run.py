from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
import socket

from nicegui import ui
from nicegui import app as ngapp

from ..utils.logging_setup import setup_logging
from .controller import UiController
from .views import build_main_view
from .app import _cleanup_logging


def _get_preferred_port() -> int:
    for var in ("TREEBOT_UI_PORT", "UI_PORT", "PORT"):
        val = os.getenv(var)
        if val:
            try:
                return int(val)
            except ValueError:
                continue
    return 8080


def _run_server(port: int) -> None:
    ngapp.on_shutdown(_cleanup_logging)
    ui.run(title="Tree Bot", reload=False, port=port)


def main() -> None:
    # Setup base logging to file/JSON to mirror service behavior if desired
    # Note: per-run logging is configured inside the pipeline when it executes
    setup_logging(Path("runs") / "ui_logs")

    controller = UiController()
    build_main_view(controller)

    # Choose port with fallbacks if busy
    start_port = _get_preferred_port()
    attempts = 10
    last_error: Optional[BaseException] = None

    def _port_free(p: int) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("0.0.0.0", p))
                return True
        except OSError:
            return False

    for i in range(attempts):
        port = start_port + i
        if not _port_free(port):
            print(f"Port {port} is busy; trying next...")
            continue
        print(f"Starting UI at http://127.0.0.1:{port}")
        try:
            _run_server(port)
            return  # server exited cleanly
        except KeyboardInterrupt:
            print("Shutting down UI gracefully...")
            _cleanup_logging()
            return
        except BaseException as e:  # pragma: no cover
            last_error = e
            continue

    if last_error is not None:
        raise SystemExit(
            f"Failed to start UI after {attempts} attempts starting at {start_port}: {last_error}"
        )


if __name__ in {"__main__", "__mp_main__"}:
    main()
