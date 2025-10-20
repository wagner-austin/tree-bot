from __future__ import annotations

from nicegui import ui


def inject_theme() -> None:
    ui.add_head_html(
        """
        <style>
          body { background: linear-gradient(135deg, #eef6ff, #f8fbff); }
          .tb-card { backdrop-filter: blur(6px); background: rgba(255,255,255,0.72); border: 1px solid rgba(11,61,145,0.08); border-radius: 12px; }
          .tb-primary { color: #0b3d91; }
          .tb-btn { background: #0b3d91 !important; color: #fff !important; }
          .tb-subtle { color: rgba(11,61,145,0.75); }
        </style>
        """
    )
