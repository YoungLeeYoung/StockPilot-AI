from typing import Any

from app.agents.contracts import AgentTool, AgentToolDefinition


class UnknownAgentToolError(LookupError):
    """Raised when a model requests a tool that is not registered."""


class AgentToolRegistry:
    def __init__(self, tools: list[AgentTool]) -> None:
        self._tools: dict[str, AgentTool] = {}
        for tool in tools:
            name = tool.definition.name
            if name in self._tools:
                raise ValueError(f"Duplicate agent tool: {name}")
            self._tools[name] = tool

    @property
    def definitions(self) -> list[AgentToolDefinition]:
        return [tool.definition for tool in self._tools.values()]

    async def execute(self, name: str, arguments: dict[str, Any]) -> Any:
        try:
            tool = self._tools[name]
        except KeyError as exc:
            raise UnknownAgentToolError(f"Unknown agent tool: {name}") from exc
        return await tool.execute(arguments)

