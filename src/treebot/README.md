# treebot package

Core application code.

- `app/`: DI container, orchestrator, run manager, steps (sheet processing), reporting helpers
- `services/`: IO, validation, transform, aggregate, and output services (single responsibility)
- `domain/`: error types and schema definitions
- `utils/`: logging setup and normalization helpers
- `main.py`: thin CLI entry delegating to the orchestrator

Extending: add a new service under `services/`, register it in `app/container.py`, and inject via the orchestrator.
