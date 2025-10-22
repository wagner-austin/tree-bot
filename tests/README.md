# tests

Test suite organized by concern:

- `services/validation/*`: header/date/numeric/keys/class consistency
- `services/transform/*`: old→new mapping, canonicalization
- `services/aggregate/*`: aggregation results and writer
- `ui/*`: controller and basic UI flows
- `integration/*`: smoke runs and end-to-end scenarios

Run with `poetry run pytest -q` or `make check`.

