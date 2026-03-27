from fastapi.testclient import TestClient

from alibaba_llm_ai_runtime.app import create_app


def test_healthz_returns_ok() -> None:
    client = TestClient(create_app())
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "alibaba-llm-ai-runtime",
        "environment": "dev",
    }
