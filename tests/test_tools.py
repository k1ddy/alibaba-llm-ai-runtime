import json
from pathlib import Path

from alibaba_llm_ai_runtime.tools import ToolExecutor


def test_tool_executor_writes_audit_records(tmp_path: Path) -> None:
    audit_path = tmp_path / "audit" / "tool-events.jsonl"
    executor = ToolExecutor(audit_path)

    result = executor.execute(
        tool_name="escalate_to_human",
        session_id="session-1",
        trace_id="trace-1",
        tool_input={
            "reason": "Need a human callback",
            "requested_by": "tester",
            "contact": "telegram:@tester",
            "confirmed": True,
        },
    )

    lines = audit_path.read_text(encoding="utf-8").strip().splitlines()
    record = json.loads(lines[0])

    assert result.status == "queued"
    assert record["tool_name"] == "escalate_to_human"
    assert record["status"] == "queued"
    assert record["detail"] == "escalation_queued"
