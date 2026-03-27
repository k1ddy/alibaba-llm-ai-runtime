from .config import Settings
from .llm import ModelClient
from .schemas import TurnRequest, TurnResponse


class SemanticOwner:
    def __init__(self, model_client: ModelClient, settings: Settings):
        self._model_client = model_client
        self._settings = settings

    async def respond(self, turn: TurnRequest, trace_id: str) -> TurnResponse:
        completion = await self._model_client.generate(
            user_message=turn.user_message,
            system_prompt=self._settings.llm_system_prompt,
            trace_id=trace_id,
            context=turn.context,
        )
        return TurnResponse(
            trace_id=trace_id,
            session_id=turn.session_id,
            outcome="answer",
            response_text=completion.text,
            model_provider=completion.provider,
            model_name=completion.model,
        )
