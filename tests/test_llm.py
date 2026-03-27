import asyncio
import json

import httpx

from alibaba_llm_ai_runtime.config import Settings
from alibaba_llm_ai_runtime.llm import (
    OpenAICompatibleChatClient,
    StubModelClient,
    build_model_client,
)
from alibaba_llm_ai_runtime.retrieval import RetrievedChunk


def test_build_model_client_defaults_to_stub() -> None:
    client = build_model_client(Settings())

    assert isinstance(client, StubModelClient)


def test_build_model_client_requires_api_key_for_live_provider() -> None:
    settings = Settings(
        llm_provider="dashscope_openai_compatible",
        llm_api_key=None,
    )

    try:
        build_model_client(settings)
    except ValueError as exc:
        assert "AI_RUNTIME_LLM_API_KEY" in str(exc)
    else:
        raise AssertionError("Expected missing API key to fail.")


def test_openai_compatible_client_parses_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/compatible-mode/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer test-key"
        assert request.headers["X-Trace-Id"] == "trace-live"

        payload = json.loads(request.content.decode())
        assert payload["model"] == "qwen-plus"
        assert "Grounded snippet" in payload["messages"][1]["content"]
        assert payload["messages"][2]["content"] == "Hello"

        return httpx.Response(
            200,
            json={
                "model": "qwen-plus",
                "choices": [
                    {
                        "message": {
                            "content": "Live adapter response",
                        }
                    }
                ],
            },
        )

    async def run() -> None:
        client = OpenAICompatibleChatClient(
            api_key="test-key",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="qwen-plus",
            timeout_seconds=5.0,
            transport=httpx.MockTransport(handler),
        )
        result = await client.generate(
            user_message="Hello",
            system_prompt="You are helpful.",
            trace_id="trace-live",
            context={},
            history=[],
            retrieval_context=[
                RetrievedChunk(
                    citation="source.md:chunk-01",
                    source_path="source.md",
                    text="Grounded snippet",
                    score=1.0,
                )
            ],
        )
        assert result.provider == "dashscope_openai_compatible"
        assert result.model == "qwen-plus"
        assert result.text == "Live adapter response"

    asyncio.run(run())
