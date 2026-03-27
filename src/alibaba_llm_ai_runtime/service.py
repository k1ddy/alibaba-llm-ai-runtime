from .config import Settings
from .llm import ModelClient
from .sessions import SessionStore
from .schemas import TurnRequest, TurnResponse


class SemanticOwner:
    def __init__(
        self,
        model_client: ModelClient,
        settings: Settings,
        session_store: SessionStore,
    ):
        self._model_client = model_client
        self._settings = settings
        self._session_store = session_store

    async def respond(self, turn: TurnRequest, trace_id: str) -> TurnResponse:
        history = self._session_store.get_history(turn.session_id)
        completion = await self._model_client.generate(
            user_message=turn.user_message,
            system_prompt=self._settings.llm_system_prompt,
            trace_id=trace_id,
            context=turn.context,
            history=history,
        )
        self._session_store.append_exchange(
            session_id=turn.session_id,
            user_message=turn.user_message,
            assistant_message=completion.text,
        )
        return TurnResponse(
            trace_id=trace_id,
            session_id=turn.session_id,
            session_turn_index=self._session_store.get_turn_count(turn.session_id),
            history_messages_used=len(history),
            outcome="answer",
            response_text=completion.text,
            model_provider=completion.provider,
            model_name=completion.model,
        )
