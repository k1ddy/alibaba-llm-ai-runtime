from fastapi.testclient import TestClient

from alibaba_llm_ai_runtime.app import app

client = TestClient(app)


def test_runtime_turn_returns_bounded_response() -> None:
    response = client.post(
        "/v1/runtime/turn",
        headers={"x-trace-id": "trace-123"},
        json={
            "session_id": "session-1",
            "user_message": "Hello",
            "context": {"channel": "demo"},
        },
    )

    payload = response.json()

    assert response.status_code == 200
    assert payload["trace_id"] == "trace-123"
    assert payload["session_id"] == "session-1"
    assert payload["outcome"] == "answer"
    assert payload["policy_state"] == "allow"
    assert payload["tools"] == []
    assert payload["citations"] == []
    assert "Runtime scaffold active" in payload["response_text"]
    assert payload["request_id"]
