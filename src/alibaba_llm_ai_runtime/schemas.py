from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    environment: str


class TurnRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)
    user_message: str = Field(min_length=1, max_length=4000)
    context: dict[str, Any] = Field(default_factory=dict)
    requested_tool: Literal["escalate_to_human"] | None = None
    tool_input: dict[str, Any] = Field(default_factory=dict)


class ToolExecutionResult(BaseModel):
    tool_name: str
    status: Literal["queued", "blocked"]
    audit_id: str
    detail: str


class TurnResponse(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    trace_id: str
    session_id: str
    session_turn_index: int
    history_messages_used: int
    outcome: Literal["answer", "action"]
    response_text: str
    model_provider: str
    model_name: str
    citations_used: int
    citations: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    tool_results: list[ToolExecutionResult] = Field(default_factory=list)
    policy_state: Literal["allow", "blocked"] = "allow"
