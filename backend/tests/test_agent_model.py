import json

import httpx
import pytest

from app.agents.contracts import AgentToolDefinition
from app.agents.models.openai_compatible import (
    AgentModelProviderError,
    OpenAICompatibleAgentModel,
)


@pytest.mark.asyncio
async def test_openai_compatible_model_parses_tool_calls() -> None:
    captured_request: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_request.update(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call-1",
                                    "type": "function",
                                    "function": {
                                        "name": "get_stock_price",
                                        "arguments": '{"symbol":"NVDA"}',
                                    },
                                }
                            ],
                        }
                    }
                ]
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    model = OpenAICompatibleAgentModel(
        base_url="https://llm.example/v1",
        api_key="test-key",
        model="test-model",
        client=client,
    )

    result = await model.complete(
        [{"role": "user", "content": "分析NVDA"}],
        [
            AgentToolDefinition(
                name="get_stock_price",
                description="Get price",
                parameters={"type": "object"},
            )
        ],
    )

    assert result.tool_calls[0].name == "get_stock_price"
    assert result.tool_calls[0].arguments == {"symbol": "NVDA"}
    assert captured_request["tool_choice"] == "auto"
    assert captured_request["model"] == "test-model"
    await client.aclose()


@pytest.mark.asyncio
async def test_openai_compatible_model_rejects_invalid_response() -> None:
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(200, json={"choices": []})
        )
    )
    model = OpenAICompatibleAgentModel(
        base_url="https://llm.example/v1",
        api_key="test-key",
        model="test-model",
        client=client,
    )

    with pytest.raises(AgentModelProviderError):
        await model.complete([], [])
    await client.aclose()

