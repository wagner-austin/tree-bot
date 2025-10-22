# app layer

Startup and orchestration.

- `container.py`: builds and wires services with explicit loggers (DI)
- `orchestrator.py`: end-to-end run (read → validate → transform/validate → outputs → aggregate)
- `steps/sheet_processing.py`: per-sheet validation/normalization step
- `reporting.py`: console formatting helpers (Rich-compatible) for clean terminal output
- `run_manager.py`: per-run directory + logging setup

Replace or extend services by editing `container.py` and updating the orchestrator.

