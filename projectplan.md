# Micro-MVP Plan (Locked) — Offline Windows

This document captures the intended micro‑MVP scope. A “Current Implementation” section summarizes how the codebase aligns today so the document remains accurate after recent refactors.

## Current Implementation (Status vs Plan)

- Multi‑sheet ingestion with schema detection (old/new) and header normalization.
- Forward‑fill of `DataFolderName` and `CartridgeNum` within a sheet; `DateRun` is not forward‑filled.
- Optional Species fill from a mapping workbook using `(Site, CartridgeNum)` keys (site inferred from sheet name). Date‑based joins are not used.
- Old->new transform: `Compound` from normalized `Match1`, `Class` via `classes.yaml`, `MatchScore` from `Match1.Quality`, and Comments header normalization.
- Outputs: one `standardized_*.xlsx` plus `run_manifest.yaml`. Summary sheets (`HQ Multiple`, `HQ Single`, `Lq Multiple`, `Lq Single`) are appended to the standardized workbook. No separate `qc_findings.xlsx` or `run_report.txt` artifacts.
- Logging: `latest_run.log` (human) and `logs.jsonl` (structured) per run.
- CLI extras: `--out`, `--max-errors`, `--quality-threshold`, `--min-count`, `--stage`.

Deferred (not yet implemented):

- Strict failure on missing Species mapping for old‑schema rows.
- Hard duplicate‑key enforcement on `(DateRun, CartridgeNum)`.
- Separate `qc_findings.xlsx` and `run_report.txt` artifacts.

---

## High‑Level Goals

- Offline Windows app (no network access required).
- Deterministic, strict processing; no silent failures.
- Read old or new schema Excel; upgrade old->new; validate new.
- Write standardized outputs, logs, and a run manifest under a timestamped run folder.
- Code quality: ruff (style) + mypy --strict (types).

## What the Micro‑MVP Does (and nothing more)

- Detect schema (old vs new) from headers.
- Upgrade old->new with exact rules (no heuristics beyond normalization):
  - Species via mapping workbook on (Site, CartridgeNum) with site inferred from sheet name.
  - Compound = normalized Match1 (name normalization only).
  - Class via exact lookup in classes.yaml (case‑insensitive after normalization). Missing -> FAIL.
  - MatchScore = numeric cast of Match1.Quality.
  - Normalize Comments; rename old long Comments header to "Comments".
- Validate:
  - Required columns and types; DateRun must parse from US M/D/YYYY and be output as ISO YYYY‑MM‑DD.
  - For new schema, Compound/Class/MatchScore are consistent with Match1, classes.yaml, Match1.Quality.
- Write outputs:
  - standardized.xlsx (new schema only, fixed column order)
  - run_manifest.yaml (versions, parameters, input checksums)
  - logs.jsonl (structured) and latest_run.log (human‑readable)
  - In the current implementation, summary sheets are appended to `standardized.xlsx`.

## Schemas

Required columns are case‑insensitive at read time, canonicalized internally.

Old schema (input):
- DataFolderName, DateRun, CartridgeNum, RetentionTime,
  Match1, Match1.Quality, Match2, Match2.Quality, Match3, Match3.Quality,
  Comments (full old header text)

New schema (input or output):
- DataFolderName, DateRun, CartridgeNum, Species, RetentionTime,
  Match1, Match1.Quality, Match2, Match2.Quality, Match3, Match3.Quality,
  Comments, Compound, Class, MatchScore

Standardized.xlsx column order (output):
- DataFolderName, DateRun, CartridgeNum, Species, RetentionTime,
  Match1, Match1.Quality, Match2, Match2.Quality, Match3, Match3.Quality,
  Comments, Compound, Class, MatchScore

## Schema Detection

- New schema if all new‑only columns are present (Species, Compound, Class, MatchScore).
- Old schema if new‑only columns are absent and old Comments header is present, or if a minimal old‑columns subset is detected.
- Mixed/ambiguous headers -> SCHEMA_ERROR.

## Deterministic Normalization (used for lookups/consistency only)

- lowercase
- trim ends
- collapse internal whitespace
- unify comma/hyphen spacing
- strip trailing punctuation/hyphens
- unicode fold (e.g., Greek letters alpha, beta)

Preserve original text in outputs except Comments normalization. All lookups use the normalized form.

## Transform Rules

- Old schema only:
  - Species: fill from mapping (Site, CartridgeNum) without overwriting existing values.
  - Compound: set to normalized(Match1); preserve original Match1.
  - Class: exact lookup in classes.yaml by normalized Compound; case‑insensitive.
  - MatchScore: numeric cast of Match1.Quality.
  - Comments: rename from old long header to "Comments" and normalize value.
- New schema:
  - Do not modify Compound, Class, MatchScore; only normalize Comments and validate consistency.

## Validation Rules

- Headers: required columns for detected schema must exist (case‑insensitive match; canonicalized internally).
- Types: RetentionTime and Match*.Quality numeric; MatchScore numeric if present; CartridgeNum treated as string.
- DateRun: input must be US M/D/YYYY; convert to ISO YYYY‑MM‑DD in output; date‑only.
- Class/Compound consistency (new schema): Class must equal classes.yaml[normalized(Compound)].
- Compound/Match1 consistency (new schema): normalized(Compound) must equal normalized(Match1).
- MatchScore consistency (new schema): MatchScore must equal numeric(Match1.Quality).

## Error Model (three categories)

- SCHEMA_ERROR — missing/wrong headers; bad types; invalid DateRun; and any new‑schema consistency violations.
- MAPPING_MISSING — required lookup not found (e.g., Compound not in classes.yaml).
- DUPLICATE_KEY — reserved; not enforced in current code.

## Inputs & Outputs

Inputs
- One results workbook (old or new schema).
- Optional mapping workbook with (Site, CartridgeNum, Species).
- classes.yaml — required for Class mapping and validation.

Outputs (under runs/<UTC timestamp>/)
- standardized_*.xlsx — standardized sheets; summary sheets appended.
- run_manifest.yaml — input paths, SHA256 checksums, pipeline_version, parameters, start/end timestamps, package versions.
- logs.jsonl — structured logs; latest_run.log — human‑readable log.

## Mapping Case Sensitivity

- Species mapping workbook: match case‑insensitively; preserve original Species text in output.
- Class mapping (classes.yaml): case‑insensitive via normalized Compound; preserve class string from map.

## Cartridge Number Handling

- CartridgeNum is treated as a string identity; trim whitespace; preserve leading zeros.

## classes.yaml Shape

Flat map of normalized compound -> class string plus optional metadata. Example:

```yaml
version: "1"
normalization: [lowercase, trim, collapse_whitespace, unify_hyphen_comma, strip_trailing_punct, fold_greek]
map:
  "octanoic acid, pentadecafluoro-, anhydride": "PFAS"
  "1,3-butadiene, 2-methyl": "Terpene"
```

## CLI

Run via Python module (packaging to .exe is a follow‑up):

```
python -m treebot.main \
  --input <results.xlsx> \
  --classes configs/classes.yaml \
  [--mapping mapping.xlsx] \
  [--out runs] \
  [--max-errors 50] \
  [--quality-threshold 80] \
  [--min-count 2] \
  [--stage full|headers]
```

## Project Layout

```
project/
  src/treebot/
    app/              # container, orchestrator, steps, run_manager
    services/         # io, validation, transform, aggregate, output
    domain/           # error categories, schema definitions
    utils/            # logging, normalization
    main.py           # CLI entry
  configs/            # config.yaml, schema.yaml, classes.yaml
  tests/              # unit and integration tests
  Makefile            # dev targets
```

## Definition of Done (MVP)

- Detects schema correctly on mixed test files.
- Upgrades old->new per rules; lists unmapped compounds in logs/summary.
- Leaves new schema unchanged (except Comments normalization and consistency validation).
- Writes standardized workbook with summary sheets, and run_manifest.yaml; logs present.
- Passes ruff and mypy --strict.
- Ready for packaging to Windows .exe (post‑MVP).

## Test Plan (tiny but meaningful)

- Smoke: old->new success with complete mapping; assert row counts and selected field values.
- Failure: missing Class mapping; expect error logged and appropriate handling.
- New schema sanity: wrong Class for a known Compound -> SCHEMA_ERROR.
- New schema consistency: mismatched Compound vs Match1 or MatchScore vs Match1.Quality -> SCHEMA_ERROR.

## Parameters and Manifest Fields (initial)

- pipeline_version
- certainty_threshold
- frequency_min
- site_mode
- strict_fail
- make_per_species_sheets
- max_errors

## Notes

- A simple local UI (NiceGUI) is provided in addition to the CLI.

