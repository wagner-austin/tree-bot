# tests

Test suite organized by concern:

- `services/validation/*`: headers, dates, keys, class map, species map
- `services/transform/*`: old->new mapping (no implicit name canonicalization)
- `utils/*`: normalization/typo safety checks
- `ui/*`: controller and basic UI flows
- `integration/*`: smoke runs and end-to-end scenarios

Run with `poetry run pytest -q` or `make check`.

