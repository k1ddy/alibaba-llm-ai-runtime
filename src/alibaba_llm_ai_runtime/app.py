from uuid import uuid4

from fastapi import FastAPI, Header, Request

from .config import Settings, get_settings
from .llm import build_model_client
from .schemas import HealthResponse, TurnRequest, TurnResponse
from .service import SemanticOwner
from .sessions import InMemorySessionStore


def create_app(settings: Settings | None = None) -> FastAPI:
    runtime_settings = settings or get_settings()
    app = FastAPI(
        title=runtime_settings.service_name,
        version="0.1.0",
        description="Bounded runtime scaffold for the Alibaba LLM platform path.",
    )
    app.state.settings = runtime_settings
    app.state.session_store = InMemorySessionStore(
        runtime_settings.session_history_max_messages
    )
    app.state.owner = SemanticOwner(
        build_model_client(runtime_settings),
        runtime_settings,
        app.state.session_store,
    )

    @app.get("/healthz", response_model=HealthResponse)
    async def healthz() -> HealthResponse:
        return HealthResponse(
            status="ok",
            service=runtime_settings.service_name,
            environment=runtime_settings.environment,
        )

    @app.post("/v1/runtime/turn", response_model=TurnResponse)
    async def runtime_turn(
        turn: TurnRequest,
        request: Request,
        x_trace_id: str | None = Header(default=None),
    ) -> TurnResponse:
        trace_id = x_trace_id or str(uuid4())
        return await request.app.state.owner.respond(turn, trace_id)

    return app


app = create_app()
