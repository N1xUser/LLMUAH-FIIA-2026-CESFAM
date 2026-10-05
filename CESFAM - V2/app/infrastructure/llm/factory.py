from app.application.interfaces.llm_provider import LLMProvider
from app.core.config import Settings
from app.domain.value_objects.model_provider import ModelProvider
from app.infrastructure.llm.claude_provider import ClaudeLLMProvider
from app.infrastructure.llm.gemini_provider import GeminiLLMProvider
from app.infrastructure.llm.local_provider import LocalLLMProvider


def build_llm_provider(settings: Settings, provider_override: ModelProvider | None = None) -> LLMProvider:

    provider = provider_override or settings.llm_provider

    if provider == ModelProvider.GEMINI:
        return GeminiLLMProvider(api_key=settings.gemini_api_key, model=settings.gemini_model)
    if provider == ModelProvider.CLAUDE:
        return ClaudeLLMProvider(api_key=settings.anthropic_api_key, model=settings.anthropic_model)
    if provider == ModelProvider.LOCAL:
        return LocalLLMProvider(base_url=settings.local_llm_base_url, model=settings.local_llm_model)

    raise ValueError(f"Proveedor de LLM no soportado: {provider}")
