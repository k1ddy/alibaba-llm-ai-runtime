from fastapi.testclient import TestClient

from alibaba_llm_ai_runtime.app import create_app


def test_runtime_turn_returns_bounded_response() -> None:
    client = TestClient(create_app())
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
    assert payload["session_turn_index"] == 1
    assert payload["history_messages_used"] == 0
    assert payload["outcome"] == "answer"
    assert payload["policy_state"] == "allow"
    assert payload["model_provider"] == "stub"
    assert payload["model_name"] == "stub-local"
    assert payload["tools"] == []
    assert payload["citations"] == []
    assert "Stub provider active" in payload["response_text"]
    assert "history_messages=0" in payload["response_text"]
    assert payload["request_id"]


def test_runtime_turn_preserves_session_history_across_turns() -> None:
    client = TestClient(create_app())

    first = client.post(
        "/v1/runtime/turn",
        headers={"x-trace-id": "trace-turn-1"},
        json={
            "session_id": "session-2",
            "user_message": "First turn",
            "context": {"channel": "demo"},
        },
    )
    second = client.post(
        "/v1/runtime/turn",
        headers={"x-trace-id": "trace-turn-2"},
        json={
            "session_id": "session-2",
            "user_message": "Second turn",
            "context": {"channel": "demo"},
        },
    )

    first_payload = first.json()
    second_payload = second.json()

    assert first.status_code == 200
    assert second.status_code == 200
    assert first_payload["session_turn_index"] == 1
    assert second_payload["session_turn_index"] == 2
    assert second_payload["history_messages_used"] == 2
    assert "history_messages=2" in second_payload["response_text"]
