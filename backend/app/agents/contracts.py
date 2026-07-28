from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class AgentToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any]


@dataclass(frozen=True, slots=True)
class AgentToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True, slots=True)
class AgentModelResponse:
    content: str | None = None
    tool_calls: list[AgentToolCall] = field(default_factory=list)


class AgentModel(Protocol):
    async def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[AgentToolDefinition],
    ) -> AgentModelResponse: ...


class AgentTool(Protocol):
    definition: AgentToolDefinition

    async def execute(self, arguments: dict[str, Any]) -> Any: ...

