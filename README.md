# Alibaba LLM AI Runtime

Minimal `FastAPI` runtime scaffold for the platform path.

## What This Repo Owns
- HTTP runtime entrypoints
- request and response schemas
- minimal semantic-owner contract
- runtime configuration
- container packaging for local and cluster execution

## What This Repo Does Not Own Yet
- retrieval pipelines
- tool servers
- eval harness
- GitOps deployment state
- Terraform-managed cloud resources

## Current Scope
This is a bounded `v1` runtime skeleton:
- `GET /healthz`
- `POST /v1/runtime/turn`
- request id and trace id handling
- deterministic placeholder response that keeps the online path explicit

## Local Run
```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
uvicorn alibaba_llm_ai_runtime.app:app --reload
```

## Tests
```bash
pytest
```
