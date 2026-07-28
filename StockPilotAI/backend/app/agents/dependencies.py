from functools import lru_cache

from app.agents.models import OpenAICompatibleAgentModel
from app.core.config import settings


class AgentConfigurationError(RuntimeError):
    """Raised when an LLM-backed feature has not been configured."""


@lru_cache
def get_agent_model() -> OpenAICompatibleAgentModel:
    if not settings.llm_base_url or not settings.llm_model:
        raise AgentConfigurationError(
            "LLM_BASE_URL and LLM_MODEL must be configured for AI analysis."
        )
    return OpenAICompatibleAgentModel(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
    )

