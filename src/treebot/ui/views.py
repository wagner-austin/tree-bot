from __future__ import annotations

from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from nicegui import ui, run as ngrun
from nicegui.events import UploadEventArguments

from ..config import Config, load_config
from .controller import UiController
from .theme import inject_theme
from .components import base_card
from .constants import default_output_base, default_uploads_dir
from .utils import open_path, save_uploaded_file


def build_main_view(controller: UiController) -> None:
    inject_theme()

    # Header
    with ui.row().classes("items-center gap-4 mb-6"):
        ui.icon("spa", size="3rem").classes("text-green-600")
        ui.label("Tree Bot").classes("text-5xl font-bold text-gray-800")

    ui.markdown("**Convert old schema workbooks to new standardized format**").classes(
        "text-lg text-gray-600 mb-8"
    )

    # State
    @dataclass
    class UiState:
        input_path: Optional[Path] = None

    state = UiState()
    default_out = default_output_base()
    default_out.mkdir(parents=True, exist_ok=True)
    classes_p = Path("configs/classes.yaml")
    mapping_path: Optional[Path] = None
    uploads_dir = default_uploads_dir()
    uploads_dir.mkdir(parents=True, exist_ok=True)

    # Upload Results Workbook
    with base_card("Upload Results Workbook", ""):
        input_label = ui.label("No file selected").classes("text-sm text-gray-500")

        def on_input_upload(e: UploadEventArguments) -> None:
            dest = save_uploaded_file(uploads_dir, e.name, e.content)
            state.input_path = dest
            input_label.text = f"✓ {dest.name}"
            input_label.classes("text-sm text-green-600")

        ui.upload(
            label="Choose .xlsx file", on_upload=on_input_upload, auto_upload=True, multiple=False
        ).props("accept=.xlsx").classes("w-full")

    # Optional Species Mapping Upload
    with base_card("Optional: Upload Species Mapping", "(Site, CartridgeNum -> PlantSpecies)"):
        map_label = ui.label("No mapping selected").classes("text-sm text-gray-500")

        def on_map_upload(e: UploadEventArguments) -> None:
            nonlocal mapping_path
            dest = save_uploaded_file(uploads_dir, e.name, e.content)
            mapping_path = dest
            map_label.text = f"Mapping: {dest.name}"
            map_label.classes("text-sm text-green-600")

        ui.upload(
            label="Choose mapping (.xlsx/.csv)",
            on_upload=on_map_upload,
            auto_upload=True,
            multiple=False,
        ).classes("w-full")

    # Process Workbook (Prominent Button)
    ui.separator().classes("my-6")

    status_container = ui.column().classes("w-full mb-4")
    with status_container:
        status = ui.label("Ready to process").classes("text-lg font-semibold text-gray-700 mb-2")

    # Big prominent button
    run_button = ui.button("▶ Process Workbook", on_click=lambda: None).classes(
        "bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 text-lg font-semibold rounded-lg shadow-lg w-full mb-6"
    )

    # Result buttons (hidden initially)
    result_row = ui.row().classes("gap-2 mb-6 hidden")

    async def do_run() -> None:
        in_path = state.input_path
        if not in_path or not in_path.exists():
            status.text = "⚠ Please upload a results workbook first"
            status.classes("text-lg font-semibold text-orange-600")
            return

        status.text = "🔄 Processing..."
        status.classes("text-lg font-semibold text-blue-600")
        status_container.update()

        cfg: Config = load_config(None)
        result = await ngrun.io_bound(
            lambda: controller.run(in_path, classes_p, default_out, cfg, mapping_path)
        )

        # Clear previous result buttons
        result_row.clear()

        if result.error:
            status.text = (
                f"❌ Pipeline Error: {result.error}\n\nCheck the run folder for logs and details."
            )
            status.classes("text-lg font-semibold text-red-600")
            if result.run_dir:
                result_row.classes(remove="hidden")
                with result_row:
                    ui.button(
                        "📂 Open Output Folder",
                        on_click=lambda rd=result.run_dir: open_path(rd),
                    ).classes("px-4 py-2")
        elif result.code == 0:
            status.text = "✅ Successfully processed! Output files ready."
            status.classes("text-lg font-semibold text-green-600")

            if result.run_dir:
                result_row.classes(remove="hidden")
                with result_row:
                    ui.button(
                        "📂 Open Output Folder",
                        on_click=lambda rd=result.run_dir: open_path(rd),
                    ).classes("bg-green-600 text-white px-4 py-2")

                    # Find latest standardized_*.xlsx in the run directory
                    try:
                        candidates = sorted(
                            [
                                p
                                for p in result.run_dir.iterdir()
                                if p.name.startswith("standardized_") and p.suffix == ".xlsx"
                            ],
                            key=lambda p: p.stat().st_mtime,
                            reverse=True,
                        )
                    except Exception:
                        candidates = []
                    if candidates:
                        latest = candidates[0]
                        ui.button(
                            "📊 Open Standardized",
                            on_click=lambda p=latest: open_path(p),
                        ).classes("bg-blue-600 text-white px-4 py-2")

                    # Manifest button intentionally hidden per UX request
        else:
            status.text = f"⚠ Processing completed with issues.\n\nThe pipeline encountered problems (exit code {result.code}). Check the output folder for logs and partial results."
            status.classes("text-lg font-semibold text-orange-600")

            if result.run_dir:
                result_row.classes(remove="hidden")
                with result_row:
                    ui.button(
                        "📂 Open Output Folder",
                        on_click=lambda rd=result.run_dir: open_path(rd),
                    ).classes("px-4 py-2")

        status_container.update()

    run_button.on("click", do_run)

    # Footer
    ui.separator().classes("my-6")
    ui.label(f"Output directory: {default_out}").classes("text-xs text-gray-500")
