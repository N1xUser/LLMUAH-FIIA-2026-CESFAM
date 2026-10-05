from abc import ABC, abstractmethod

from app.domain.entities.document import RetrievedChunk


class VectorRepository(ABC):
    @abstractmethod
    async def similarity_search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        document_id: str | None = None,
    ) -> list[RetrievedChunk]: ...
