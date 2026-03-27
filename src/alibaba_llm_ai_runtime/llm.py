from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from .config import Settings
from .retrieval import RetrievedChunk
from .sessions import SessionMessage


@dataclass(frozen=True)
class ModelCompletion:
    text: str
    provider: str
    model: str


class ModelClient(Protocol):
    async def generate(
        self,
        *,
        user_message: str,
        system_prompt: str,
        trace_id: str,
        context: dict[str, Any],
        history: list[SessionMessage],
        retrieval_context: list[RetrievedChunk],
    ) -> ModelCompletion: ...


class StubModelClient:
    provider = "stub"
    model = "stub-local"

    async def generate(
        self,
        *,
        user_message: str,
        system_prompt: str,
        trace_id: str,
        context: dict[str, Any],
        history: list[SessionMessage],
        retrieval_context: list[RetrievedChunk],
    ) -> ModelCompletion:
        context_keys = ", ".join(sorted(context)) if context else "none"
        history_messages = len(history)
        retrieved_chunks = len(retrieval_context)
        first_citation = retrieval_context[0].citation if retrieval_context else "none"
        text = (
            "Stub provider active. "
            f"message={user_message!r}; context_keys={context_keys}; "
            f"history_messages={history_messages}; retrieved_chunks={retrieved_chunks}; "
            f"first_citation={first_citation}; trace_id={trace_id}. "
            "Tools are still disabled."
        )
        return ModelCompletion(text=text, provider=self.provider, model=self.model)


class OpenAICompatibleChatClient:
    provider = "dashscope_openai_compatible"

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        timeout_seconds: float,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._transport = transport

    async def generate(
        self,
        *,
        user_message: str,
        system_prompt: str,
        trace_id: str,
        context: dict[str, Any],
        history: list[SessionMessage],
        retrieval_context: list[RetrievedChunk],
    ) -> ModelCompletion:
        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
        if retrieval_context:
            messages.append(
                {
                    "role": "system",
                    "content": _format_grounding_context(retrieval_context),
                }
            )
        messages.extend(
            {"role": message.role, "content": message.content} for message in history
        )
        messages.append({"role": "user", "content": user_message})
        payload = {"model": self._model, "messages": messages}
        async with httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout_seconds,
            transport=self._transport,
        ) as client:
            response = await client.post(
                "/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "X-Trace-Id": trace_id,
                },
                json=payload,
            )
            response.raise_for_status()

        data = response.json()
        return ModelCompletion(
            text=_extract_text(data),
            provider=self.provider,
            model=data.get("model", self._model),
        )


def build_model_client(
    settings: Settings,
    *,
    transport: httpx.AsyncBaseTransport | None = None,
) -> ModelClient:
    if settings.llm_provider == "stub":
        return StubModelClient()
    if settings.llm_provider == "dashscope_openai_compatible":
        if not settings.llm_api_key:
            raise ValueError(
                "AI_RUNTIME_LLM_API_KEY is required when "
                "AI_RUNTIME_LLM_PROVIDER=dashscope_openai_compatible."
            )
        return OpenAICompatibleChatClient(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            model=settings.llm_model,
            timeout_seconds=settings.llm_timeout_seconds,
            transport=transport,
        )
    raise ValueError(f"Unsupported llm provider: {settings.llm_provider}")


def _extract_text(response_json: dict[str, Any]) -> str:
    choices = response_json.get("choices") or []
    if not choices:
        return "Model returned an empty response."

    content = choices[0].get("message", {}).get("content", "")
    if isinstance(content, str):
        text = content.strip()
    elif isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
        text = "".join(parts).strip()
    else:
        text = str(content).strip()

    return text or "Model returned an empty response."


def _format_grounding_context(retrieval_context: list[RetrievedChunk]) -> str:
    lines = ["Use only the grounded context below when answering."]
    for item in retrieval_context:
        lines.append(f"[{item.citation}] {item.text}")
    return "\n".join(lines)
