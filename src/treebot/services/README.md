# services

Stateless, focused services with explicit logger injection via the container.

- `io_excel.py`: read/detect schema, write standardized Excel
- `validation/`: small rule modules (headers, dates, numeric, keys, class_map, consistency)
- `validate_service.py`: thin facade over rule modules
- `transform_service.py`: old→new migration + comments normalization
- `aggregate/`: aggregation service + writer (Summary, Out_<Site>, canonicalization report, stats)
- `output_service.py`: QC findings, run report, manifest writers

Add new capabilities as separate services and register them in `app/container.py`.

