PYTHON ?= python3
VENV ?= .venv

.PHONY: venv install test run quality

venv:
	$(PYTHON) -m venv $(VENV)

install: venv
	. $(VENV)/bin/activate && pip install --upgrade pip && pip install -e '.[dev]'

test:
	. $(VENV)/bin/activate && pytest

run:
	. $(VENV)/bin/activate && uvicorn alibaba_llm_ai_runtime.app:app --reload

quality:
	. $(VENV)/bin/activate && python scripts/run_quality.py --run-id local-quality
