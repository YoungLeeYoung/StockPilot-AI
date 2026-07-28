import json
from typing import Any

import httpx

from app.agents.contracts import (
    AgentModelResponse,
    AgentToolCall,
    AgentToolDefinition,
)


class AgentModelProviderError(RuntimeError):
    """Raised when an OpenAI-compatible model endpoint fails or returns invalid data."""


class OpenAICompatibleAgentModel:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float = 60,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not base_url.strip() or not model.strip():
            raise ValueError("LLM base URL and model are required.")
        self.endpoint = f"{base_url.rstrip('/')}/chat/completions"
        self.api_key = api_key
        self.model = model
        self.client = client or httpx.AsyncClient(timeout=timeout_seconds)
        self._owns_client = client is None

    async def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[AgentToolDefinition],
    ) -> AgentModelResponse:
        payload = {
            "model": self.model,
            "messages": [self._format_message(message) for message in messages],
            "tools": [self._format_tool(tool) for tool in tools],
            "tool_choice": "auto",
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            response = await self.client.post(self.endpoint, json=payload, headers=headers)
            response.raise_for_status()
            body = response.json()
            message = body["choices"][0]["message"]
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            raise AgentModelProviderError("LLM provider request failed.") from exc

        tool_calls: list[AgentToolCall] = []
        for raw_call in message.get("tool_calls") or []:
            try:
                arguments = json.loads(raw_call["function"]["arguments"] or "{}")
                if not isinstance(arguments, dict):
                    raise TypeError("Tool arguments must be an object.")
                tool_calls.append(
                    AgentToolCall(
                        id=raw_call["id"],
                        name=raw_call["function"]["name"],
                        arguments=arguments,
                    )
                )
            except (json.JSONDecodeError, KeyError, TypeError) as exc:
                raise AgentModelProviderError("LLM returned an invalid tool call.") from exc

        content = message.get("content")
        if content is not None and not isinstance(content, str):
            raise AgentModelProviderError("LLM returned invalid message content.")
        return AgentModelResponse(content=content, tool_calls=tool_calls)

    async def close(self) -> None:
        if self._owns_client:
            await self.client.aclose()

    @staticmethod
    def _format_tool(tool: AgentToolDefinition) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            },
        }

    @staticmethod
    def _format_message(message: dict[str, Any]) -> dict[str, Any]:
        if message.get("role") != "assistant" or not message.get("tool_calls"):
            return message

        formatted = dict(message)
        formatted["tool_calls"] = [
            {
                "id": call["id"],
                "type": "function",
                "function": {
                    "name": call["name"],
                    "arguments": json.dumps(call["arguments"], ensure_ascii=False),
                },
            }
            for call in message["tool_calls"]
        ]
        return formatted

