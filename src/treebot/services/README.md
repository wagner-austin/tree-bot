# services

Stateless, focused services with explicit logger injection via the container.

- `io_excel.py`: read/detect schema, write standardized Excel
- `validation/`: rule modules (headers, dates, keys, class_map, species_map)
- `validate_service.py`: thin facade over rule modules (forward-fill identities, apply species mapping, load class map)
- `transform_service.py`: old->new migration (derive Compound, Class, MatchScore)
- `aggregate/summary.py`: build per-site/per-species compound summaries
- `output/summary_writer.py`: append summary sections to standardized workbook
- `output/manifest_writer.py`: write per-run `run_manifest.yaml`

Add new capabilities as separate services and register them in `app/container.py`.

