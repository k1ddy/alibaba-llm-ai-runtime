from .config import Settings
from .llm import ModelClient
from .retrieval import LocalFileRetriever
from .sessions import SessionStore
from .schemas import TurnRequest, TurnResponse


class SemanticOwner:
    def __init__(
        self,
        model_client: ModelClient,
        settings: Settings,
        session_store: SessionStore,
        retriever: LocalFileRetriever,
    ):
        self._model_client = model_client
        self._settings = settings
        self._session_store = session_store
        self._retriever = retriever

    async def respond(self, turn: TurnRequest, trace_id: str) -> TurnResponse:
        history = self._session_store.get_history(turn.session_id)
        retrieval_hits = self._retriever.search(
            turn.user_message,
            top_k=self._settings.retrieval_top_k,
        )
        if not retrieval_hits:
            fallback = "I don't know based on the current local knowledge base."
            self._session_store.append_exchange(
                session_id=turn.session_id,
                user_message=turn.user_message,
                assistant_message=fallback,
            )
            return TurnResponse(
                trace_id=trace_id,
                session_id=turn.session_id,
                session_turn_index=self._session_store.get_turn_count(turn.session_id),
                history_messages_used=len(history),
                outcome="answer",
                response_text=fallback,
                model_provider="retrieval-fallback",
                model_name="none",
                citations_used=0,
                citations=[],
            )

        completion = await self._model_client.generate(
            user_message=turn.user_message,
            system_prompt=self._settings.llm_system_prompt,
            trace_id=trace_id,
            context=turn.context,
            history=history,
            retrieval_context=retrieval_hits,
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
            citations_used=len(retrieval_hits),
            citations=[item.citation for item in retrieval_hits],
        )
