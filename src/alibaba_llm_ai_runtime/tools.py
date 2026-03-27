import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from .schemas import ToolExecutionResult


class EscalateToHumanInput(BaseModel):
    reason: str = Field(min_length=3, max_length=500)
    requested_by: str = Field(min_length=1, max_length=128)
    contact: str = Field(min_length=3, max_length=128)
    confirmed: bool = False


@dataclass(frozen=True)
class AuditEvent:
    audit_id: str
    timestamp_utc: str
    session_id: str
    trace_id: str
    tool_name: str
    status: Literal["queued", "blocked"]
    payload: dict[str, Any]
    detail: str


class ToolExecutor:
    def __init__(self, audit_log_path: str | Path):
        self._audit_log_path = Path(audit_log_path)

    def execute(
        self,
        *,
        tool_name: str,
        session_id: str,
        trace_id: str,
        tool_input: dict[str, Any],
    ) -> ToolExecutionResult:
        if tool_name != "escalate_to_human":
            raise ValueError(f"Unsupported tool: {tool_name}")

        payload = EscalateToHumanInput.model_validate(tool_input)
        if not payload.confirmed:
            return self._write_event(
                session_id=session_id,
                trace_id=trace_id,
                tool_name=tool_name,
                status="blocked",
                payload=payload.model_dump(),
                detail="confirmation_required",
            )

        return self._write_event(
            session_id=session_id,
            trace_id=trace_id,
            tool_name=tool_name,
            status="queued",
            payload=payload.model_dump(),
            detail="escalation_queued",
        )

    def _write_event(
        self,
        *,
        session_id: str,
        trace_id: str,
        tool_name: str,
        status: Literal["queued", "blocked"],
        payload: dict[str, Any],
        detail: str,
    ) -> ToolExecutionResult:
        event = AuditEvent(
            audit_id=str(uuid4()),
            timestamp_utc=datetime.now(UTC).isoformat(),
            session_id=session_id,
            trace_id=trace_id,
            tool_name=tool_name,
            status=status,
            payload=payload,
            detail=detail,
        )
        self._audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        with self._audit_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(event), ensure_ascii=True) + "\n")

        return ToolExecutionResult(
            tool_name=tool_name,
            status=status,
            audit_id=event.audit_id,
            detail=detail,
        )
