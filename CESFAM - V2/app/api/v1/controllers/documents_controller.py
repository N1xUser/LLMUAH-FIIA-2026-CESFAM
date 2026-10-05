from fastapi import APIRouter, Depends, UploadFile

from app.api.deps import get_ingestion_service
from app.api.v1.schemas.document_schema import DocumentResponse
from app.application.services.ingestion_service import IngestionService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile, ingestion_service: IngestionService = Depends(get_ingestion_service)
) -> DocumentResponse:
    raw_bytes = await file.read()
    document = await ingestion_service.ingest_document(
        filename=file.filename or "documento",
        content_type=file.content_type or "text/plain",
        raw_bytes=raw_bytes,
    )
    return DocumentResponse(id=document.id, filename=document.filename, content_type=document.content_type)
