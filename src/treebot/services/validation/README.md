# validation rules

Small, composable rule modules used by `ValidateService`.

- `headers.py`: canonicalize headers, ensure required columns
- `dates.py`: `DateRun` parsing (US M/D/YYYY → ISO)
- `keys.py`: `CartridgeNum` trimming and forward-fill helpers
- `class_map.py`: load `classes.yaml` (keys normalized via `normalize_compound_name`)
- `species_map.py`: load/apply species mapping workbook (Site, CartridgeNum → PlantSpecies)

Prefer adding a module per concern over growing a single file.

