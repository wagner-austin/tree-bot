# Tree Bot

Offline Windows app (local UI + CLI) to validate and transform Excel workbooks (old/new schema). Produces a standardized row-level workbook and a manifest. No network access required; packaging to .exe follows validation.

## Quick Start (Dev)

- Requires Python 3.10+ and Poetry
- Install deps: `poetry install`
- UI: `make run` (starts local NiceGUI at http://localhost:8080)
- CLI: `poetry run python -m treebot.main --input path\to\results.xlsx --classes configs\classes.yaml [--mapping mapping.xlsx] [--config configs\config.yaml] [--out runs] [--max-errors 50] [--quality-threshold 80] [--min-count 2] [--stage full|headers]`

Outputs are written to `./runs/<UTC timestamp>/`.

### CLI Arguments

- `--input`: Results workbook (.xlsx)
- `--classes`: Path to `classes.yaml` (Compound -> Class mapping; keys must match normalized compound names)
- `--mapping` (optional): Species mapping workbook (columns: `Site`, `CartridgeNum`, `PlantSpecies`). Used to fill missing `Species` without overwriting existing values.
- `--config` (optional): YAML config file with runtime overrides
- `--out` (optional): Output base directory (`runs` by default)
- `--max-errors` (optional): Limit for errors shown in logs/reports
- `--quality-threshold` (optional): Minimum MatchScore for “high quality” groups in summary
- `--min-count` (optional): Minimum frequency per compound for summary sheets
- `--stage` (optional): `headers` to validate headers only, or `full` (default)

## Packaging

Packaging to a single Windows `.exe` is planned after validation.

## Architecture

- `src/treebot/app/`: container, orchestrator, run manager, modular steps (sheet processing)
- `src/treebot/services/`: IO, validation rules+service, transform, aggregation (`aggregate/summary.py`), output utilities (manifest, summary writer)
- `src/treebot/domain/`: error categories and issue types
- `src/treebot/utils/`: logging, normalization helpers
- `src/treebot/main.py`: thin CLI entrypoint
- `configs/classes.yaml`: Compound -> Class map (keys must be normalized; see Normalization)
- `tests/`: unit + integration tests

See `projectplan.md` for design scope; note the “Current Implementation” section for deviations.

## Config

- File-based only (no env vars). Example: `configs/config.yaml`
- `configs/classes.yaml` maps normalized Compound -> Class
- Optional species mapping workbook (`--mapping`) can fill missing Species using `(Site, CartridgeNum) -> PlantSpecies` pairs.


## Make Targets (PowerShell)

- `make check` — poetry lock, install, ruff fix/format, mypy --strict, pytest
- `make run` — starts the local UI (NiceGUI)
- `make run-cli INPUT=... [CLASSES=...] [MAPPING=...] [OUT=runs] [CONFIG=...]` — run from terminal
- `make lock` — update Poetry lock

## Outputs

- `standardized_*.xlsx` (row-level output, when no blocking errors). Summary sheets (`HQ Multiple`, `HQ Single`, `Lq Multiple`, `Lq Single`) are appended to this workbook.
- `run_manifest.yaml` (provenance, parameters)
- Logs: `latest_run.log` (human) and `logs.jsonl` (structured)

## Console Logs

- Rich-styled sections for skipped sheets and validation warnings (empty Species, CartridgeNum, DataFolderName; empty Quality columns)

## Pipeline Behavior

1. Detect schema per sheet and normalize headers
2. Forward-fill identity columns within a sheet (DataFolderName, CartridgeNum)
3. Optionally fill missing `Species` via mapping workbook (no overwrite)
4. For old schema sheets, transform to new schema and derive `Compound`, `Class`, and `MatchScore`
5. Write `standardized_*.xlsx`
6. Build and append summary sheets; write `run_manifest.yaml`

## Normalization

- Compound names are normalized with a safe, non-destructive function (`normalize_compound_name`):
  - Unicode normalize (NFKC), fold Greek letters, lowercase/trim
  - Two-pass typo handling: embedded-safe replacements, then token-bounded regex fixes
  - Remove bare stereochem markers like `(r)`, `(s)`, unify spacing/hyphens, strip trailing noise
  - Does not change chemical identity or apply synonym mapping
- Class mapping keys in `classes.yaml` must match the normalized form.
- Name canonicalization (global synonym mapping) is not performed inside the transform pipeline.

### Auditing Class Mappings

- `scripts/audit_class_mappings.py` prints distribution and highlights entries to review.
