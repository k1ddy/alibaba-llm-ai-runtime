import logging
from uuid import uuid4

from fastapi import FastAPI, Header, Request

from .config import Settings, get_settings
from .llm import build_model_client
from .observability import JsonlEventLogger
from .retrieval import LocalFileRetriever
from .schemas import HealthResponse, TurnRequest, TurnResponse
from .service import SemanticOwner
from .sessions import InMemorySessionStore
from .tools import ToolExecutor


def create_app(settings: Settings | None = None) -> FastAPI:
    runtime_settings = settings or get_settings()
    logging.basicConfig(level=getattr(logging, runtime_settings.log_level.upper(), logging.INFO))
    app = FastAPI(
        title=runtime_settings.service_name,
        version="0.1.0",
        description="Bounded runtime scaffold for the Alibaba LLM platform path.",
    )
    app.state.settings = runtime_settings
    app.state.session_store = InMemorySessionStore(
        runtime_settings.session_history_max_messages
    )
    app.state.event_logger = JsonlEventLogger(
        service_name=runtime_settings.service_name,
        environment=runtime_settings.environment,
        log_path=runtime_settings.observability_log_path,
    )
    app.state.owner = SemanticOwner(
        build_model_client(runtime_settings),
        runtime_settings,
        app.state.session_store,
        LocalFileRetriever(runtime_settings.knowledge_source_dir),
        ToolExecutor(runtime_settings.tool_audit_log_path),
        app.state.event_logger,
    )

    @app.get("/healthz", response_model=HealthResponse)
    async def healthz() -> HealthResponse:
        app.state.event_logger.emit(
            event_type="health_checked",
            payload={"status": "ok"},
        )
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
