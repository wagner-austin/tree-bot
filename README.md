# Tree Bot

Offline Windows app (local UI + CLI) to validate, transform, and aggregate Excel workbooks (old/new schema). Produces standardized row‑level output, aggregated reports, QC artifacts, and a manifest. No network access required; packaging to .exe follows validation.

## Quick Start (Dev)

- Requires Python 3.10+ and Poetry
- Install deps: `poetry install`
- UI: `make run` (opens local NiceGUI at http://localhost:8080)
- CLI: `poetry run python -m treebot.main --input path\to\results.xlsx --classes configs\classes.yaml [--mapping mapping.xlsx] [--config configs\config.yaml]`

Outputs are written to `./runs/<UTC timestamp>/`.

## Packaging

Packaging to a single Windows `.exe` is planned after validation.

## Architecture

- `src/treebot/app/`: container, orchestrator, run manager, modular steps (sheet processing), console reporting helpers
- `src/treebot/services/`: io, validation rules+service, transform, aggregate, output service
- `src/treebot/domain/`: error categories and issue types
- `src/treebot/utils/`: logging, normalization helpers
- `src/treebot/main.py`: thin CLI entrypoint
- `configs/classes.yaml`: Compound → Class map
- `tests/`: unit + integration tests

See `projectplan.md` for locked requirements.

## Config

- File-based only (no env vars). Example: `configs/config.yaml`
- `configs/classes.yaml` maps normalized Compound → Class

## Make Targets (PowerShell)

- `make check` → poetry lock, install, ruff fix/format, mypy --strict, pytest
- `make run` → converts maps, starts local UI (NiceGUI) and opens browser
- `make run-cli INPUT=… [CLASSES=…] [MAPPING=…] [OUT=runs] [CONFIG=…]` → run from terminal
- `make lock` → update Poetry lock

## Outputs

- `standardized.xlsx` (row‑level, when no blocking errors)
- `aggregated.xlsx` (Summary + Out_<Site> sheets, canonicalization report, stats)
- `qc_findings.xlsx` (summary, duplicates, unmapped compounds, skipped_sheets, schema_errors)
- `run_report.txt` (human summary)
- `run_manifest.yaml` (provenance, params, hashes)

## Console Logs

- Rich‑styled sections for skipped sheets, duplicate keys, and final failure summary
- Duplicate key alias: “Primary Key columns: Site/DataFolderName + DateRun + CartridgeNum + Compound”

