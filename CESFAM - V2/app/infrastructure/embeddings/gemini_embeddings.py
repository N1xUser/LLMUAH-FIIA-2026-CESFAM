from google import genai
from google.genai import types

from app.application.interfaces.embedding_provider import EmbeddingProvider
from app.core.exceptions import ProviderError


_MAX_EMBED_BATCH_SIZE = 100


class GeminiEmbeddingProvider(EmbeddingProvider):
    def __init__(self, api_key: str, model: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def embed_text(self, text: str) -> list[float]:
        result = await self._client.aio.models.embed_content(model=self._model, contents=text)
        return result.embeddings[0].values

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        all_vectors: list[list[float]] = []
        for start in range(0, len(texts), _MAX_EMBED_BATCH_SIZE):
            batch = texts[start : start + _MAX_EMBED_BATCH_SIZE]
            all_vectors.extend(await self._embed_batch_chunk(batch))
        return all_vectors

    async def _embed_batch_chunk(self, texts: list[str]) -> list[list[float]]:
  
        contents = [types.Content(parts=[types.Part.from_text(text=t)]) for t in texts]
        result = await self._client.aio.models.embed_content(model=self._model, contents=contents)
        embeddings = result.embeddings

        if len(embeddings) != len(texts):
            raise ProviderError(
                f"Gemini devolvió {len(embeddings)} embeddings para {len(texts)} "
                f"textos enviados en el batch (modelo '{self._model}'). Esto "
                "normalmente significa que el modelo no soporta batch real vía "
                "embed_content — revisa la documentación vigente antes de seguir."
            )
        return [e.values for e in embeddings]