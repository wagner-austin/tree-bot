# validation rules

Small, composable rule modules used by `ValidateService`.

- `headers.py`: canonicalize headers, ensure required columns
- `dates.py`: `DateRun` parsing (US M/D/YYYY → ISO)
- `numeric.py`: numeric column checks
- `keys.py`: `(DateRun, CartridgeNum)` trimming and duplicate detection
- `class_map.py`: load classes.yaml (normalized map)
- `consistency.py`: new schema consistency checks

Prefer adding a module per concern over growing a single file.

