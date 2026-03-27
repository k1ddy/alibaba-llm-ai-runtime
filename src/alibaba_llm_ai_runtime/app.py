from uuid import uuid4

from fastapi import FastAPI, Header

from .config import get_settings
from .llm import build_model_client
from .schemas import HealthResponse, TurnRequest, TurnResponse
from .service import SemanticOwner

settings = get_settings()
owner = SemanticOwner(build_model_client(settings), settings)

app = FastAPI(
    title=settings.service_name,
    version="0.1.0",
    description="Bounded runtime scaffold for the Alibaba LLM platform path.",
)


@app.get("/healthz", response_model=HealthResponse)
async def healthz() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.service_name,
        environment=settings.environment,
    )


@app.post("/v1/runtime/turn", response_model=TurnResponse)
async def runtime_turn(
    turn: TurnRequest,
    x_trace_id: str | None = Header(default=None),
) -> TurnResponse:
    trace_id = x_trace_id or str(uuid4())
    return await owner.respond(turn, trace_id)
