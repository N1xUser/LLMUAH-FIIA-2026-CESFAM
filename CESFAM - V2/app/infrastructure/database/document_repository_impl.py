from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.domain.entities.document import Document, DocumentChunk
from app.domain.repositories.document_repository import DocumentRepository


class MongoDocumentRepository(DocumentRepository):
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._documents = db["documents"]
        self._chunks = db["document_chunks"]

    async def save_document(self, document: Document) -> Document:
        data = document.model_dump(exclude={"id"})
        result = await self._documents.insert_one(data)
        document.id = str(result.inserted_id)
        return document

    async def save_chunks(self, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        if not chunks:
            return []
        payload = [c.model_dump(exclude={"id"}) for c in chunks]
        result = await self._chunks.insert_many(payload)
        for chunk, inserted_id in zip(chunks, result.inserted_ids):
            chunk.id = str(inserted_id)
        return chunks

    async def get_document(self, document_id: str) -> Document | None:
        raw = await self._documents.find_one({"_id": ObjectId(document_id)})
        if raw is None:
            return None
        raw["id"] = str(raw.pop("_id"))
        return Document(**raw)

    async def list_documents(self) -> list[Document]:
        docs: list[Document] = []
        async for raw in self._documents.find():
            raw["id"] = str(raw.pop("_id"))
            docs.append(Document(**raw))
        return docs

    async def delete_document(self, document_id: str) -> None:
        await self._documents.delete_one({"_id": ObjectId(document_id)})
        await self._chunks.delete_many({"document_id": document_id})
