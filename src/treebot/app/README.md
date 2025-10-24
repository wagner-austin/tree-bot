# app layer

Startup and orchestration.

- `container.py`: builds and wires services with explicit loggers (DI)
- `orchestrator.py`: end-to-end run (read + normalize headers + forward-fill identities + species mapping (optional) + old->new transform + outputs + summary sheets)
- `steps/sheet_processing.py`: per-sheet normalization, forward-fill, optional species mapping
- `run_manager.py`: per-run directory + logging setup
- `../services/aggregate/summary.py`: build per-site/per-species compound summaries
- `../services/output/summary_writer.py`: append summary sections to the standardized workbook

Outputs written by the orchestrator:

- `standardized_*.xlsx`
- `run_manifest.yaml`
- Summary sheets are appended to the standardized workbook: `HQ Multiple`, `HQ Single`, `Lq Multiple`, `Lq Single`.

Replace or extend services by editing `container.py` and updating the orchestrator.

