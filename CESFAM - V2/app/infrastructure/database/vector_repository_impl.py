import numpy as np
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.domain.entities.document import DocumentChunk, RetrievedChunk
from app.domain.repositories.vector_repository import VectorRepository


class MongoVectorRepository(VectorRepository):

    def __init__(self, db: AsyncIOMotorDatabase, backend: str = "atlas", index_name: str = "vector_index") -> None:
        self._collection = db["document_chunks"]
        self._backend = backend
        self._index_name = index_name

    async def similarity_search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        document_id: str | None = None,
    ) -> list[RetrievedChunk]:
        if self._backend == "atlas":
            return await self._atlas_search(query_embedding, top_k, document_id)
        return await self._brute_force_search(query_embedding, top_k, document_id)

    async def _atlas_search(
        self, query_embedding: list[float], top_k: int, document_id: str | None
    ) -> list[RetrievedChunk]:
        vector_search_stage: dict = {
            "$vectorSearch": {
                "index": self._index_name,
                "path": "embedding",
                "queryVector": query_embedding,
                "numCandidates": max(top_k * 10, 50),
                "limit": top_k,
            }
        }
        if document_id:
            vector_search_stage["$vectorSearch"]["filter"] = {"document_id": {"$eq": document_id}}

        pipeline = [
            vector_search_stage,
            {"$set": {"score": {"$meta": "vectorSearchScore"}}},
        ]
        results = []
        async for raw in self._collection.aggregate(pipeline):
            score = raw.pop("score")
            raw["id"] = str(raw.pop("_id"))
            results.append(RetrievedChunk(chunk=DocumentChunk(**raw), score=score))
        return results

    async def _brute_force_search(
        self, query_embedding: list[float], top_k: int, document_id: str | None
    ) -> list[RetrievedChunk]:
        query_vec = np.array(query_embedding)
        query_norm = np.linalg.norm(query_vec) or 1e-8

        filters = {"document_id": document_id} if document_id else {}
        scored: list[RetrievedChunk] = []
        async for raw in self._collection.find(filters):
            raw["id"] = str(raw.pop("_id"))
            chunk = DocumentChunk(**raw)
            chunk_vec = np.array(chunk.embedding)
            chunk_norm = np.linalg.norm(chunk_vec) or 1e-8
            score = float(np.dot(query_vec, chunk_vec) / (query_norm * chunk_norm))
            scored.append(RetrievedChunk(chunk=chunk, score=score))

        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:top_k]
