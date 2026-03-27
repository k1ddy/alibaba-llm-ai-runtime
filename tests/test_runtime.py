from pathlib import Path

from fastapi.testclient import TestClient

from alibaba_llm_ai_runtime.app import create_app
from alibaba_llm_ai_runtime.config import Settings


def test_runtime_turn_returns_bounded_response() -> None:
    settings = _settings_with_demo_knowledge()
    client = TestClient(create_app(settings))
    response = client.post(
        "/v1/runtime/turn",
        headers={"x-trace-id": "trace-123"},
        json={
            "session_id": "session-1",
            "user_message": "Which repository owns cloud foundation resources?",
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
    assert payload["citations_used"] == 1
    assert payload["citations"] == ["platform-overview.md:chunk-02"]
    assert "Stub provider active" in payload["response_text"]
    assert "history_messages=0" in payload["response_text"]
    assert "retrieved_chunks=1" in payload["response_text"]
    assert payload["request_id"]


def test_runtime_turn_preserves_session_history_across_turns() -> None:
    settings = _settings_with_demo_knowledge()
    client = TestClient(create_app(settings))

    first = client.post(
        "/v1/runtime/turn",
        headers={"x-trace-id": "trace-turn-1"},
        json={
            "session_id": "session-2",
            "user_message": "What is the first product target?",
            "context": {"channel": "demo"},
        },
    )
    second = client.post(
        "/v1/runtime/turn",
        headers={"x-trace-id": "trace-turn-2"},
        json={
            "session_id": "session-2",
            "user_message": "How should the assistant answer?",
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
    assert second_payload["citations_used"] == 1
    assert second_payload["citations"]


def test_runtime_turn_returns_grounded_fallback_when_no_documents_match() -> None:
    settings = _settings_with_demo_knowledge()
    client = TestClient(create_app(settings))

    response = client.post(
        "/v1/runtime/turn",
        headers={"x-trace-id": "trace-no-hit"},
        json={
            "session_id": "session-3",
            "user_message": "Need CUDA workstation advice",
            "context": {"channel": "demo"},
        },
    )

    payload = response.json()

    assert response.status_code == 200
    assert payload["model_provider"] == "retrieval-fallback"
    assert payload["model_name"] == "none"
    assert payload["citations_used"] == 0
    assert payload["citations"] == []
    assert payload["response_text"] == "I don't know based on the current local knowledge base."


def test_runtime_turn_executes_explicit_tool_and_writes_audit(tmp_path: Path) -> None:
    settings = _settings_with_demo_knowledge(tmp_path)
    client = TestClient(create_app(settings))

    response = client.post(
        "/v1/runtime/turn",
        headers={"x-trace-id": "trace-tool-1"},
        json={
            "session_id": "session-tool-1",
            "user_message": "Please escalate this issue.",
            "requested_tool": "escalate_to_human",
            "tool_input": {
                "reason": "Customer needs a human callback",
                "requested_by": "demo-user",
                "contact": "telegram:@demo",
                "confirmed": True,
            },
            "context": {"channel": "demo"},
        },
    )

    payload = response.json()
    audit_lines = settings.tool_audit_log_path

    assert response.status_code == 200
    assert payload["outcome"] == "action"
    assert payload["policy_state"] == "allow"
    assert payload["model_provider"] == "tool-executor"
    assert payload["tools"] == ["escalate_to_human"]
    assert payload["tool_results"][0]["status"] == "queued"
    assert Path(audit_lines).exists()


def test_runtime_turn_blocks_tool_without_confirmation(tmp_path: Path) -> None:
    settings = _settings_with_demo_knowledge(tmp_path)
    client = TestClient(create_app(settings))

    response = client.post(
        "/v1/runtime/turn",
        headers={"x-trace-id": "trace-tool-2"},
        json={
            "session_id": "session-tool-2",
            "user_message": "Escalate now.",
            "requested_tool": "escalate_to_human",
            "tool_input": {
                "reason": "Customer asks for a manager",
                "requested_by": "demo-user",
                "contact": "telegram:@demo",
                "confirmed": False,
            },
            "context": {"channel": "demo"},
        },
    )

    payload = response.json()

    assert response.status_code == 200
    assert payload["outcome"] == "action"
    assert payload["policy_state"] == "blocked"
    assert payload["tool_results"][0]["status"] == "blocked"
    assert payload["response_text"] == "Tool request blocked: confirmation required."


def _settings_with_demo_knowledge(tmp_path: Path | None = None) -> Settings:
    knowledge_dir = Path(__file__).resolve().parents[1] / "knowledge" / "source"
    audit_path = (
        tmp_path / "tool-events.jsonl"
        if tmp_path is not None
        else Path("runtime_data/audit/tool-events.jsonl")
    )
    return Settings(
        knowledge_source_dir=str(knowledge_dir),
        retrieval_top_k=1,
        tool_audit_log_path=str(audit_path),
    )
