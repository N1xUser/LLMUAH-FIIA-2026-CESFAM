from app.application.interfaces.embedding_provider import EmbeddingProvider


class LocalEmbeddingProvider(EmbeddingProvider):

    def __init__(self, model_name: str) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise ImportError(
                "sentence-transformers no está instalado. Ejecuta: "
                "pip install -r requirements-local.txt"
            ) from exc
        self._model = SentenceTransformer(model_name)

    async def embed_text(self, text: str) -> list[float]:
        return self._model.encode(text, normalize_embeddings=True).tolist()

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return self._model.encode(texts, normalize_embeddings=True).tolist()
