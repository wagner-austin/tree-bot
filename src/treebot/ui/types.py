from __future__ import annotations

from typing import Protocol, BinaryIO


class UploadEvent(Protocol):
    name: str
    content: bytes | BinaryIO
