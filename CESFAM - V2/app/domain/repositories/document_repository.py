from abc import ABC, abstractmethod

from app.domain.entities.document import Document, DocumentChunk


class DocumentRepository(ABC):
    @abstractmethod
    async def save_document(self, document: Document) -> Document: ...

    @abstractmethod
    async def save_chunks(self, chunks: list[DocumentChunk]) -> list[DocumentChunk]: ...

    @abstractmethod
    async def get_document(self, document_id: str) -> Document | None: ...

    @abstractmethod
    async def list_documents(self) -> list[Document]: ...

    @abstractmethod
    async def delete_document(self, document_id: str) -> None: ...
