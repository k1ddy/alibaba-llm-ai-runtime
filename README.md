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
- локальный bounded tool path с audit trail
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
- `AI_RUNTIME_TOOL_AUDIT_LOG_PATH=runtime_data/audit/tool-events.jsonl`
- `AI_RUNTIME_OBSERVABILITY_LOG_PATH=runtime_data/observability/runtime-events.jsonl`

Опциональный live adapter path:
- `AI_RUNTIME_LLM_PROVIDER=dashscope_openai_compatible`
- `AI_RUNTIME_LLM_API_KEY=<твой Model Studio key>`
- `AI_RUNTIME_LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1`

Важно:
- локально ключ можно держать в `.env`;
- для cluster deploy ключ должен приходить через Kubernetes `Secret`, а не через `ConfigMap`.

## Тесты
```bash
pytest
```

Проверка компиляции исходников:
```bash
python -m compileall src tests scripts
```

## Quality / Regression
Локальный quality-контур запускается так:
```bash
python scripts/run_quality.py --run-id local-quality
```

Golden dataset лежит в:
- `quality/golden_cases.json`

## Локальный Источник Знаний
Текущий source-of-truth для bounded demo лежит в:
- `knowledge/source/`

Retrieval index пока строится только в памяти при старте runtime и не сохраняется отдельно.

## Локальный Tool Boundary
Сейчас доступен один bounded local tool:
- `escalate_to_human`

Это explicit action path:
- tool вызывается только через `requested_tool`;
- tool пишет audit trail в локальный `jsonl` файл;
- risky action требует `confirmed=true`.

## Локальная Наблюдаемость
Runtime пишет structured execution events в локальный `jsonl` файл:
- `health_checked`
- `turn_received`
- `retrieval_completed`
- `tool_executed`
- `turn_completed`

## Delivery / CI
Минимальный delivery-контур теперь живёт в GitHub Actions:
- `.github/workflows/ci.yml`

Что делает pipeline:
- ставит зависимости;
- проверяет компиляцию исходников;
- запускает `pytest`;
- запускает local quality harness;
- собирает Docker image;
- делает container smoke check;
- сохраняет quality-артефакты workflow.

Локальная проверка тех же шагов:
```bash
make install
make compile
make test
make quality
make docker-build
make smoke-container
```


## Image Publishing
Для container image выбран минимальный и дешёвый путь через `GitHub Container Registry`:
- registry path: `ghcr.io/k1ddy/alibaba-llm-ai-runtime`

Текущая tagging discipline:
- `main` — moving tag для последнего успешного publish с default branch;
- `sha-<shortsha>` — immutable tag для конкретного коммита.

Что делает publish boundary:
- после успешного `verify` job публикует image в `GHCR`;
- не делает rollout в cluster;
- не меняет GitOps tag автоматически.

Практический смысл:
- CI теперь выдаёт не только проверенный build, но и publish-ready artifact;
- GitOps позже сможет ссылаться либо на `main`, либо на конкретный `sha-*` tag.

## Registry Path Для Alibaba
Для live deploy в `ACK cn-hangzhou` путь через `GHCR` оказался ненадёжным: первый cluster delivery завис на image pull.

Поэтому текущая инженерная стратегия такая:
- `GHCR` остаётся как low-friction publish path для CI и внешней проверки;
- для live deploy в Alibaba нужен более локальный registry path через `ACR`.

CI уже готов к optional publish в `ACR`, если задать GitHub secrets:
- `ACR_REGISTRY`
- `ACR_USERNAME`
- `ACR_PASSWORD`
- `ACR_NAMESPACE`

Для `ACR_REGISTRY` используй именно login server твоего инстанса.
Для новых `Personal Edition` это обычно формат:
- `crpi-<instance-id>.cn-hangzhou.personal.cr.aliyuncs.com`

Ожидаемый image path после включения `ACR`:
- `<ACR_REGISTRY>/<ACR_NAMESPACE>/alibaba-llm-ai-runtime:main`
- `<ACR_REGISTRY>/<ACR_NAMESPACE>/alibaba-llm-ai-runtime:sha-<shortsha>`

Важно:
- для budget-first demo разумно начинать с `Container Registry Personal Edition`;
- для live `ACK` path в `cn-hangzhou` именно `ACR` считается основным рабочим вариантом;
- после появления `ACR` надо переключить `dev` overlay в GitOps repo с `GHCR` на `ACR`.
