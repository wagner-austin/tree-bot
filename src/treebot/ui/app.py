from __future__ import annotations


def _cleanup_logging() -> None:
    import logging

    logger = logging.getLogger()
    for h in list(logger.handlers):
        try:
            h.flush()
        except Exception:
            pass
        try:
            h.close()
        except Exception:
            pass
        try:
            logger.removeHandler(h)
        except Exception:
            pass
