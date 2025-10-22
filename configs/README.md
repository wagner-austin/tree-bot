# configs

Runtime configuration and reference maps.

- `config.yaml`: runtime parameters (no env vars)
- `classes.yaml`: normalized `Compound` → `Class` map used for validation and old→new transform

Guidance:

- Class map keys must match the pipeline’s normalized form of compound names (see Normalization in the root README).
- The Python pipeline does not perform name canonicalization (synonym mapping); use explicit keys in `classes.yaml`.
- Optional species mapping workbook can be supplied at runtime via `--mapping` (columns: `Site`, `CartridgeNum`, `PlantSpecies`).

Note: `name_canonicalization.yaml` is currently not used by the Python pipeline.

