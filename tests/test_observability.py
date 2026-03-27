import json
from pathlib import Path

from fastapi.testclient import TestClient

from alibaba_llm_ai_runtime.app import create_app
from alibaba_llm_ai_runtime.config import Settings


def test_runtime_writes_observability_events_for_answer_path(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    client = TestClient(create_app(settings))

    health = client.get("/healthz")
    answer = client.post(
        "/v1/runtime/turn",
        headers={"x-trace-id": "trace-obs-answer"},
        json={
            "session_id": "obs-answer-1",
            "user_message": "Which repository owns cloud foundation resources?",
            "context": {"channel": "observability"},
        },
    )

    assert health.status_code == 200
    assert answer.status_code == 200

    lines = _read_events(Path(settings.observability_log_path))
    event_types = [line["event_type"] for line in lines]

    assert "health_checked" in event_types
    assert "turn_received" in event_types
    assert "retrieval_completed" in event_types
    assert "turn_completed" in event_types


def test_runtime_writes_observability_events_for_action_path(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    client = TestClient(create_app(settings))

    action = client.post(
        "/v1/runtime/turn",
        headers={"x-trace-id": "trace-obs-action"},
        json={
            "session_id": "obs-action-1",
            "user_message": "Please escalate this issue.",
            "requested_tool": "escalate_to_human",
            "tool_input": {
                "reason": "Customer needs a human callback",
                "requested_by": "observability-user",
                "contact": "telegram:@observability",
                "confirmed": True,
            },
            "context": {"channel": "observability"},
        },
    )

    assert action.status_code == 200

    lines = _read_events(Path(settings.observability_log_path))
    tool_events = [line for line in lines if line["event_type"] == "tool_executed"]

    assert tool_events
    assert tool_events[0]["payload"]["tool_status"] == "queued"


def _read_events(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _settings(tmp_path: Path) -> Settings:
    repo_root = Path(__file__).resolve().parents[1]
    return Settings(
        knowledge_source_dir=str(repo_root / "knowledge" / "source"),
        tool_audit_log_path=str(tmp_path / "tool-events.jsonl"),
        observability_log_path=str(tmp_path / "runtime-events.jsonl"),
        retrieval_top_k=1,
    )
