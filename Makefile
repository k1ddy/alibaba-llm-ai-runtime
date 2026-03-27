PYTHON ?= python3
VENV ?= .venv

.PHONY: venv install compile test run quality docker-build smoke-container

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

compile:
	. $(VENV)/bin/activate && python -m compileall src tests scripts

docker-build:
	docker build -t alibaba-llm-ai-runtime:local .

smoke-container:
	./scripts/smoke_container.sh alibaba-llm-ai-runtime:local
