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
- configurable `LLM` provider boundary
- deterministic `stub` mode by default
- optional `DashScope` OpenAI-compatible adapter path

## Local Run
```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
uvicorn alibaba_llm_ai_runtime.app:app --reload
```

## Provider Configuration
Copy `.env.example` to `.env` and adjust only when you want live model calls.

Default local-safe mode:
- `AI_RUNTIME_LLM_PROVIDER=stub`

Optional live adapter path:
- `AI_RUNTIME_LLM_PROVIDER=dashscope_openai_compatible`
- `AI_RUNTIME_LLM_API_KEY=<your-model-studio-key>`
- `AI_RUNTIME_LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1`

## Tests
```bash
pytest
```
