from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass(frozen=True)
class SessionMessage:
    role: Literal["user", "assistant"]
    content: str


class SessionStore(Protocol):
    def get_history(self, session_id: str) -> list[SessionMessage]: ...

    def append_exchange(
        self,
        *,
        session_id: str,
        user_message: str,
        assistant_message: str,
    ) -> None: ...

    def get_turn_count(self, session_id: str) -> int: ...


class InMemorySessionStore:
    def __init__(self, max_messages_per_session: int = 12):
        if max_messages_per_session < 2:
            raise ValueError("max_messages_per_session must be at least 2.")
        self._messages: dict[str, deque[SessionMessage]] = defaultdict(
            lambda: deque(maxlen=max_messages_per_session)
        )

    def get_history(self, session_id: str) -> list[SessionMessage]:
        return list(self._messages[session_id])

    def append_exchange(
        self,
        *,
        session_id: str,
        user_message: str,
        assistant_message: str,
    ) -> None:
        history = self._messages[session_id]
        history.append(SessionMessage(role="user", content=user_message))
        history.append(SessionMessage(role="assistant", content=assistant_message))

    def get_turn_count(self, session_id: str) -> int:
        return len(self._messages[session_id]) // 2
