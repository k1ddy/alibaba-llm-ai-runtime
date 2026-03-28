FROM python:3.12-slim

WORKDIR /app

LABEL org.opencontainers.image.source="https://github.com/k1ddy/alibaba-llm-ai-runtime"
LABEL org.opencontainers.image.description="Minimal FastAPI runtime for the Alibaba LLM platform path"

COPY pyproject.toml README.md ./
COPY src ./src
COPY knowledge ./knowledge

RUN pip install --no-cache-dir .

EXPOSE 8080

CMD ["uvicorn", "alibaba_llm_ai_runtime.app:app", "--host", "0.0.0.0", "--port", "8080"]
