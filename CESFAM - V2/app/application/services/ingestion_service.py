from app.application.interfaces.embedding_provider import EmbeddingProvider
from app.domain.entities.document import Document, DocumentChunk
from app.domain.repositories.document_repository import DocumentRepository


def _extract_text(raw_bytes: bytes, content_type: str) -> str:
    if _looks_like_pdf(raw_bytes, content_type):
        return _extract_pdf_text(raw_bytes)
    return raw_bytes.decode("utf-8", errors="ignore")


def _looks_like_pdf(raw_bytes: bytes, content_type: str) -> bool:
   
    if content_type == "application/pdf":
        return True
    return raw_bytes[:5] == b"%PDF-"


def _extract_pdf_text(raw_bytes: bytes) -> str:
   
    from io import BytesIO

    from pypdf import PdfReader

    reader = PdfReader(BytesIO(raw_bytes))
    parts: list[str] = [
        page_text.strip()
        for page in reader.pages
        if (page_text := (page.extract_text() or "")).strip()
    ]

    parts.extend(_extract_tables_as_markdown(raw_bytes))

    return "\n\n".join(parts)


def _extract_tables_as_markdown(raw_bytes: bytes) -> list[str]:
   
    from io import BytesIO

    import pdfplumber

    blocks: list[str] = []
    with pdfplumber.open(BytesIO(raw_bytes)) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            if not tables:
                tables = page.extract_tables(
                    table_settings={
                        "vertical_strategy": "text",
                        "horizontal_strategy": "text",
                    }
                )

            for table in tables:
                markdown_table = _table_to_markdown(table)
                if markdown_table:
                    blocks.append(f"[Tabla en página {page_number}]\n{markdown_table}")
    return blocks


def _table_to_markdown(table: list[list[str | None]]) -> str:
    rows = [
        [(cell or "").strip() for cell in row]
        for row in table
        if any(cell and cell.strip() for cell in row)
    ]
    if not rows:
        return ""

    header, *body = rows
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(["---"] * len(header)) + " |",
    ]
    for row in body:
        padded = row + [""] * (len(header) - len(row))
        lines.append("| " + " | ".join(padded[: len(header)]) + " |")
    return "\n".join(lines)


def _chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
   
    blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
    if not blocks:
        return []

    chunks: list[str] = []
    current: list[str] = []
    current_words = 0

    for block in blocks:
        block_words = len(block.split())
        if current and current_words + block_words > chunk_size:
            chunks.append("\n\n".join(current))
            
            current = [current[-1]] if overlap > 0 else []
            current_words = len(current[-1].split()) if current else 0
        current.append(block)
        current_words += block_words

    if current:
        chunks.append("\n\n".join(current))

    return chunks


class IngestionService:

    def __init__(self, document_repository: DocumentRepository, embedding_provider: EmbeddingProvider) -> None:
        self._documents = document_repository
        self._embeddings = embedding_provider

    async def ingest_document(self, filename: str, content_type: str, raw_bytes: bytes) -> Document:
        text = _extract_text(raw_bytes, content_type)
        document = await self._documents.save_document(
            Document(filename=filename, content_type=content_type)
        )

        pieces = _chunk_text(text)
        if not pieces:
            return document

        vectors = await self._embeddings.embed_batch(pieces)
        chunks = [
            DocumentChunk(document_id=document.id, chunk_index=i, content=piece, embedding=vector)
            for i, (piece, vector) in enumerate(zip(pieces, vectors))
        ]
        await self._documents.save_chunks(chunks)
        return document