from __future__ import annotations

import logging
from dataclasses import dataclass

from ..config import Config
from ..services.io_excel import IOService
from ..services.transform_service import TransformService
from ..services.validate_service import ValidateService


@dataclass(frozen=True)
class Container:
    io: IOService
    validate: ValidateService
    transform: TransformService


def build_container(base_logger_name: str, cfg: Config) -> Container:
    base = logging.getLogger(base_logger_name)
    io = IOService(base.getChild("io"))
    validate = ValidateService(base.getChild("validate"))
    transform = TransformService(base.getChild("transform"))
    return Container(io=io, validate=validate, transform=transform)
