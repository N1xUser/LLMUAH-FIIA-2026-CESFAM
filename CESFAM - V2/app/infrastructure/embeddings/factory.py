from app.application.interfaces.embedding_provider import EmbeddingProvider
from app.core.config import Settings
from app.infrastructure.embeddings.gemini_embeddings import GeminiEmbeddingProvider
from app.infrastructure.embeddings.local_embeddings import LocalEmbeddingProvider


def build_embedding_provider(settings: Settings) -> EmbeddingProvider:
    if settings.embedding_provider == "local":
        return LocalEmbeddingProvider(settings.local_embedding_model)
    return GeminiEmbeddingProvider(api_key=settings.gemini_api_key, model=settings.gemini_embedding_model)
