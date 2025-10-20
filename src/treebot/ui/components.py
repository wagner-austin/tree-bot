from __future__ import annotations

from typing import Optional

from nicegui import ui


def base_card(title: str, subtitle: Optional[str] = None) -> ui.card:
    card = ui.card().classes("tb-card max-w-3xl w-full shadow-md")
    with card:
        ui.label(title).classes("text-xl font-semibold tb-primary")
        if subtitle:
            ui.label(subtitle).classes("text-sm tb-subtle")
    return card
