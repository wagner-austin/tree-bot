.PHONY: check run install lock lint format mypy test

POETRY ?= poetry

# Defaults for convenience
CLASSES ?= configs\classes.yaml
OUT ?= runs
CONFIG ?= configs\config.yaml

install:
	$(POETRY) install

lock:
	$(POETRY) lock

lint:
	-$(POETRY) run ruff check --fix .
	-$(POETRY) run ruff format .

format:
	-$(POETRY) run ruff format .

mypy:
	$(POETRY) run mypy --strict

test:
	$(POETRY) run pytest -q

check: lock install lint mypy test

# Usage:
# make run INPUT=path\to\results.xlsx CLASSES=configs\classes.yaml [MAPPING=path\to\mapping.xlsx] [OUT=runs]
ifdef MAPPING
MAPARG=--mapping $(MAPPING)
endif
ifdef OUT
OUTARG=--out $(OUT)
endif
ifdef CONFIG
CFGARG=--config $(CONFIG)
endif

run: lock install
	$(POETRY) run python -m treebot.ui.run

.PHONY: run-cli
run-cli: lock install
ifeq ($(strip $(INPUT)),)
	$(error Usage: make run-cli INPUT=path\to\results.xlsx [CLASSES=configs\classes.yaml] [MAPPING=path\to\mapping.xlsx] [OUT=runs] [CONFIG=configs\config.yaml])
endif
	$(POETRY) run python -m treebot.main --input $(INPUT) --classes $(CLASSES) $(MAPARG) $(OUTARG) $(CFGARG)
