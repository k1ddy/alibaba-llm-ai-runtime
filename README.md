# Alibaba LLM AI Runtime

Минимальный runtime-репозиторий на `FastAPI` для platform path.

## Что Этот Репозиторий Делает
- HTTP runtime entrypoints;
- request/response schemas;
- semantic-owner contract;
- runtime configuration;
- container packaging для локального запуска и будущего запуска в кластере.

## Что Этот Репозиторий Пока Не Делает
- не хранит retrieval pipelines как отдельный ingestion layer;
- не хранит tool servers;
- не хранит eval harness;
- не хранит GitOps deployment state;
- не управляет Terraform-ресурсами.

## Текущее Состояние
Сейчас это bounded `v1` runtime:
- `GET /healthz`
- `POST /v1/runtime/turn`
- request id и trace id handling
- bounded in-memory session state
- локальный file-based retrieval с citations
- configurable `LLM` provider boundary
- безопасный `stub` path по умолчанию
- optional `DashScope` OpenAI-compatible adapter path

## Локальный Запуск
```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
uvicorn alibaba_llm_ai_runtime.app:app --reload
```

## Конфигурация Провайдера
Скопируй `.env.example` в `.env` и меняй настройки только если нужен live model path.

Безопасный локальный режим:
- `AI_RUNTIME_LLM_PROVIDER=stub`
- `AI_RUNTIME_SESSION_HISTORY_MAX_MESSAGES=12`
- `AI_RUNTIME_KNOWLEDGE_SOURCE_DIR=knowledge/source`
- `AI_RUNTIME_RETRIEVAL_TOP_K=2`

Опциональный live adapter path:
- `AI_RUNTIME_LLM_PROVIDER=dashscope_openai_compatible`
- `AI_RUNTIME_LLM_API_KEY=<твой Model Studio key>`
- `AI_RUNTIME_LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1`

## Тесты
```bash
pytest
```

## Локальный Источник Знаний
Текущий source-of-truth для bounded demo лежит в:
- `knowledge/source/`

Retrieval index пока строится только в памяти при старте runtime и не сохраняется отдельно.
