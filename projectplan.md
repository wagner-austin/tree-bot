# Micro-MVP Plan (Locked) — Offline Windows

This document locks the micro-MVP scope and rules for an offline Windows CLI tool that validates and transforms Excel workbooks into a standardized schema, with strict logging and repeatability. Packaging to a single .exe comes after MVP validation.

## High-Level Goals
- Offline Windows app (no network access required).
- Deterministic, strict processing; no silent failures.
- Read old or new schema Excel; upgrade old→new; validate new.
- Write standardized outputs, logs, and a run manifest under a timestamped run folder.
- Code quality: ruff (style) + mypy --strict (types).

## What the Micro-MVP Does (and nothing more)
- Detect schema (old vs new) from headers.
- Upgrade old→new with exact rules (no heuristics beyond normalization):
  - Species via mapping workbook on (DateRun, CartridgeNum). Missing → FAIL.
  - Compound = normalized Match1 (name normalization only).
  - Class via exact lookup in classes.yaml (case-insensitive after normalization). Missing → FAIL.
  - MatchScore = numeric cast of Match1.Quality.
  - Normalize Comments; rename old long Comments header to "Comments".
- Validate:
  - Required columns and types; DateRun must parse from US M/D/YYYY and be output as ISO YYYY-MM-DD.
  - (DateRun, CartridgeNum) unique.
  - For new schema, Compound/Class/MatchScore are consistent with Match1, classes.yaml, Match1.Quality.
- Write outputs:
  - standardized.xlsx (new schema only, fixed column order)
  - qc_findings.xlsx (summary + details, including unmapped compounds)
  - run_report.txt (terse counts + examples)
  - run_manifest.yaml (versions, parameters, input checksums)
  - logs.jsonl (structured) and latest_run.log (human-readable)

## Schemas
Required columns are case-insensitive at read time, canonicalized internally.

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
- New schema if all new-only columns are present (Species, Compound, Class, MatchScore).
- Old schema if new-only columns are absent and old Comments header is present.
- Mixed/ambiguous headers → SCHEMA_ERROR.

## Deterministic Normalization (used for lookups/consistency only)
- lowercase
- trim ends
- collapse internal whitespace
- unify comma/hyphen spacing
- strip trailing punctuation/hyphens
- unicode fold (e.g., Greek letters α→alpha, β→beta)

Preserve original text in outputs except Comments normalization. All lookups use the normalized form.

## Transform Rules
- Old schema only:
  - Species: join mapping workbook on (DateRun, CartridgeNum).
  - Compound: set to normalized(Match1) but preserve original Match1 in Match1 column; Compound holds the normalized name.
  - Class: exact lookup in classes.yaml by normalized Compound; case-insensitive; preserve class string from map.
  - MatchScore: numeric cast of Match1.Quality.
  - Comments: rename from old long header to "Comments" and normalize value.
- New schema:
  - Do not modify Compound, Class, MatchScore values; only normalize Comments (content) and validate consistency.

## Validation Rules
- Headers: required columns for detected schema must exist (case-insensitive match, canonicalized internally to exact names above).
- Types: RetentionTime and Match*.Quality numeric; MatchScore numeric if present; CartridgeNum treated as string.
- DateRun: input must be US M/D/YYYY; convert to ISO YYYY-MM-DD in output; treat as date-only (no time zone).
- Key uniqueness: (DateRun, CartridgeNum) must be unique across the input.
- Class/Compound consistency (new schema): Class must equal classes.yaml[normalized(Compound)]; mismatch → SCHEMA_ERROR.
- Compound/Match1 consistency (new schema): normalized(Compound) must equal normalized(Match1); mismatch → SCHEMA_ERROR.
- MatchScore consistency (new schema): MatchScore must equal numeric(Match1.Quality); mismatch → SCHEMA_ERROR.

## Error Model (three categories)
- SCHEMA_ERROR — missing/wrong headers; bad types; invalid DateRun; duplicates in required columns; and any new-schema consistency violations.
- MAPPING_MISSING — required lookup not found:
  - Old schema: missing Species for (DateRun, CartridgeNum) in mapping workbook.
  - Any schema: Compound not found in classes.yaml for normalized name.
- DUPLICATE_KEY — duplicate (DateRun, CartridgeNum).

Policy: Any of these FAIL the run (no standardized.xlsx). qc_findings.xlsx and logs still produced for diagnosis.

## Inputs & Outputs
Inputs
- One results workbook (old or new schema).
- Mapping workbook with (DateRun, CartridgeNum, Species) — required if any old-schema rows are processed.
- classes.yaml — required for Class mapping and validation.

Outputs (under runs/<UTC timestamp>/)
- standardized.xlsx — new schema only, fixed column order.
- qc_findings.xlsx — sheets:
  - summary (counts by category)
  - unmapped_compounds (unique list + frequency)
  - duplicates ((DateRun, CartridgeNum) rows)
  - schema_errors (first N examples per check)
- run_report.txt — terse counts + first N rows per failure category.
- run_manifest.yaml — input paths, SHA256 checksums, pipeline_version, parameters, start/end timestamps, package versions.
- logs.jsonl — structured logs; latest_run.log — human-readable log.

## Mapping Case Sensitivity
- Species mapping workbook: match case-insensitively; preserve original Species text in output.
- Class mapping (classes.yaml): case-insensitive via normalized Compound; preserve class string from map.

## Cartridge Number Handling
- CartridgeNum is treated as a string identity; trim whitespace; preserve leading zeros.

## classes.yaml Shape
Flat map of normalized compound → class string plus optional metadata. Example:

```yaml
version: "1"
normalization: [lowercase, trim, collapse_whitespace, unify_hyphen_comma, strip_trailing_punct, fold_greek]
map:
  "octanoic acid, pentadecafluoro-, anhydride": "PFAS"
  "1,3-butadiene, 2-methyl": "Terpene"
```

## CLI
Run via Python module (packaging to .exe is next step after MVP):

```
python -m treebot.main \
  --input <results.xlsx> \
  --classes configs/classes.yaml \
  [--mapping mapping.xlsx] \
  [--out runs] \
  [--max-errors 50]
```

Fail early if old schema detected and --mapping is missing.

## Project Layout

```
project/
  src/
    mvp.py             # orchestrator (parse args, call steps, exit codes)
    io_excel.py        # read inputs, write outputs
    validate.py        # header/type checks, key uniqueness, map checks
    transform.py       # old→new migration, normalization
    logging_setup.py   # JSON + human logger configuration
  configs/
    classes.yaml       # Compound → Class dictionary (authoritative)
  tests/
    test_smoke.py      # 3–4 high-value tests with tiny fixtures
  pyproject.toml       # ruff + mypy(strict) + pytest config
  README.md            # how to run locally (pre-packaging)
```

## Definition of Done (MVP)
- Detects schema correctly on mixed test files.
- Upgrades old→new per rules; FAIL if Species or Class mapping missing; list all unmapped compounds.
- Leaves new schema unchanged (except Comments normalization and consistency validation).
- Writes standardized.xlsx, qc_findings.xlsx, run_report.txt, run_manifest.yaml, logs.
- All logic passes ruff and mypy --strict.
- Ready to run on clean Windows via packaging to .exe in next step (no Python required post-packaging).

## Test Plan (tiny but meaningful)
- Smoke: old→new success with complete mapping; assert row counts and selected field values.
- Failure: missing Species mapping; expect MAPPING_MISSING and no standardized.xlsx.
- Failure: duplicate (DateRun, CartridgeNum); expect DUPLICATE_KEY.
- New schema sanity: wrong Class for a known Compound → SCHEMA_ERROR.
- New schema consistency: mismatched Compound vs Match1 or MatchScore vs Match1.Quality → SCHEMA_ERROR.
- Unmapped compounds listing: qc_findings.xlsx contains all unique unmapped compounds with frequencies.

## Parameters and Manifest Fields (initial)
- pipeline_version: v1.0
- certainty_threshold: 80 (if used later; recorded in manifest)
- frequency_min: 2 (if used later; recorded in manifest)
- site_mode: sheetname (record in manifest if relevant)
- strict_fail: TRUE (implicit by model)
- make_per_species_sheets: TRUE/FALSE (not used in MVP; record default if present)

## Notes
- No UI, no warnings tier, no SQLite/CSV extras; a single standardized Excel and QC/supporting outputs.
- No heavy frameworks (no pandera/pydantic yet); explicit, readable checks.
- Packaging to Windows .exe follows after MVP validation.
