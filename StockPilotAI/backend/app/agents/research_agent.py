import asyncio
import json
from typing import Any

from pydantic import ValidationError

from app.agents.contracts import AgentModel, AgentModelResponse, AgentToolCall
from app.agents.tool_registry import AgentToolRegistry
from app.schemas.research import InvestmentResearchReport

RESEARCH_SYSTEM_PROMPT = """
你是 StockPilot AI 的股票研究 Agent。
你的任务是帮助用户理解市场信息，而不是预测涨跌或给出个性化买卖指令。

你可以自主选择和调用工具。对于完整的股票研究请求，应在形成结论前收集：股票价格与基础信息、技术指标、近期新闻、公司财报信息。工具调用顺序由你根据上下文决定；当资料不足或工具失败时，必须明确说明限制，禁止编造数据。

最终只返回符合以下字段的 JSON：
company_overview, current_trend, technical_analysis, news_impact, risk_factors, summary。
risk_factors 必须是字符串数组，其他字段是字符串。
报告应区分事实、分析和不确定性，并避免确定性收益承诺。
""".strip()


class ResearchAgentError(Exception):
    """Base exception for research agent failures."""


class AgentIterationLimitError(ResearchAgentError):
    """Raised when the model does not finish within the configured iteration limit."""


class AgentOutputError(ResearchAgentError):
    """Raised when the model returns an invalid final report."""


class ResearchAgent:
    def __init__(
        self,
        model: AgentModel,
        tools: AgentToolRegistry,
        max_iterations: int = 8,
    ) -> None:
        if max_iterations < 1:
            raise ValueError("max_iterations must be positive")
        self.model = model
        self.tools = tools
        self.max_iterations = max_iterations

    async def run(self, user_input: str) -> InvestmentResearchReport:
        query = user_input.strip()
        if not query:
            raise ValueError("User input cannot be empty.")

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": RESEARCH_SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ]

        for _ in range(self.max_iterations):
            response = await self.model.complete(messages, self.tools.definitions)
            if response.tool_calls:
                messages.append(self._assistant_tool_call_message(response))
                tool_messages = await asyncio.gather(
                    *(self._execute_tool(call) for call in response.tool_calls)
                )
                messages.extend(tool_messages)
                continue

            if response.content:
                return self._parse_report(response.content)

            raise AgentOutputError("Agent model returned neither tool calls nor a report.")

        raise AgentIterationLimitError(
            f"Agent did not finish within {self.max_iterations} iterations."
        )

    async def _execute_tool(self, call: AgentToolCall) -> dict[str, Any]:
        try:
            result = await self.tools.execute(call.name, call.arguments)
            content = {"ok": True, "data": result}
        except Exception as exc:
            content = {
                "ok": False,
                "error": type(exc).__name__,
                "message": str(exc),
            }
        return {
            "role": "tool",
            "tool_call_id": call.id,
            "name": call.name,
            "content": json.dumps(content, ensure_ascii=False, default=str),
        }

    @staticmethod
    def _assistant_tool_call_message(response: AgentModelResponse) -> dict[str, Any]:
        return {
            "role": "assistant",
            "content": response.content,
            "tool_calls": [
                {
                    "id": call.id,
                    "name": call.name,
                    "arguments": call.arguments,
                }
                for call in response.tool_calls
            ],
        }

    @staticmethod
    def _parse_report(content: str) -> InvestmentResearchReport:
        normalized = content.strip()
        if normalized.startswith("```"):
            lines = normalized.splitlines()
            normalized = "\n".join(lines[1:-1]).strip()

        try:
            payload = json.loads(normalized)
            return InvestmentResearchReport.model_validate(payload)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise AgentOutputError("Agent returned an invalid research report.") from exc
