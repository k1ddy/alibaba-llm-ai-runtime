from .schemas import TurnRequest, TurnResponse


class SemanticOwner:
    def respond(self, turn: TurnRequest, trace_id: str) -> TurnResponse:
        message = (
            "Runtime scaffold active. RAG and tool execution are not enabled yet. "
            "This endpoint only proves the bounded online path."
        )
        return TurnResponse(
            trace_id=trace_id,
            session_id=turn.session_id,
            outcome="answer",
            response_text=message,
        )
