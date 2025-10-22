# app layer

Startup and orchestration.

- `container.py`: builds and wires services with explicit loggers (DI)
- `orchestrator.py`: end-to-end run (read → normalize headers → forward-fill identities → species mapping (optional) → old→new transform → outputs)
- `steps/sheet_processing.py`: per-sheet normalization, forward-fill, optional species mapping
- `reporting.py`: console formatting helpers (Rich-compatible) for clean terminal output
- `run_manager.py`: per-run directory + logging setup

Outputs written by the orchestrator:

- `standardized_*.xlsx`
- `run_manifest.yaml`

There is no Python aggregation step in the orchestrator. Aggregation can be run via external tooling (see `ExampleAggregateScript.ts`).

Replace or extend services by editing `container.py` and updating the orchestrator.

