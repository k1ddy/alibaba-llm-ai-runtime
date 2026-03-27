from alibaba_llm_ai_runtime.sessions import InMemorySessionStore


def test_in_memory_session_store_trims_old_messages() -> None:
    store = InMemorySessionStore(max_messages_per_session=4)

    store.append_exchange(
        session_id="session-1",
        user_message="turn-1-user",
        assistant_message="turn-1-assistant",
    )
    store.append_exchange(
        session_id="session-1",
        user_message="turn-2-user",
        assistant_message="turn-2-assistant",
    )
    store.append_exchange(
        session_id="session-1",
        user_message="turn-3-user",
        assistant_message="turn-3-assistant",
    )

    history = store.get_history("session-1")

    assert [message.content for message in history] == [
        "turn-2-user",
        "turn-2-assistant",
        "turn-3-user",
        "turn-3-assistant",
    ]
    assert store.get_turn_count("session-1") == 2
