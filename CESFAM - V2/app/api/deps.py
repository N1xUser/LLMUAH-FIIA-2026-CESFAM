from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.application.services.chat_service import ChatService
from app.application.services.ingestion_service import IngestionService
from app.application.services.rag_service import RAGService
from app.application.services.whatsapp_service import WhatsAppService
from app.core.config import Settings, get_settings
from app.infrastructure.database.conversation_repository_impl import MongoConversationRepository
from app.infrastructure.database.document_repository_impl import MongoDocumentRepository
from app.infrastructure.database.mongo_client import get_database
from app.infrastructure.database.vector_repository_impl import MongoVectorRepository
from app.infrastructure.embeddings.factory import build_embedding_provider
from app.infrastructure.llm.factory import build_llm_provider
from app.infrastructure.messaging.meta_whatsapp_provider import MetaWhatsAppProvider
from app.infrastructure.speech.factory import build_stt_provider, build_tts_provider






def get_db() -> AsyncIOMotorDatabase:
    return get_database()


def get_document_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> MongoDocumentRepository:
    return MongoDocumentRepository(db)


def get_conversation_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> MongoConversationRepository:
    return MongoConversationRepository(db)


def get_vector_repository(
    db: AsyncIOMotorDatabase = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> MongoVectorRepository:
    return MongoVectorRepository(
        db, backend=settings.vector_search_backend, index_name=settings.mongo_vector_index
    )


def get_embedding_provider(settings: Settings = Depends(get_settings)):
    return build_embedding_provider(settings)


def get_llm_provider(settings: Settings = Depends(get_settings)):
    return build_llm_provider(settings)


def get_stt_provider(settings: Settings = Depends(get_settings)):
    return build_stt_provider(settings)


def get_tts_provider(settings: Settings = Depends(get_settings)):
    return build_tts_provider(settings)


def get_messaging_provider(settings: Settings = Depends(get_settings)) -> MetaWhatsAppProvider:
    return MetaWhatsAppProvider(
        access_token=settings.meta_access_token,
        phone_number_id=settings.meta_phone_number_id,
        api_version=settings.meta_api_version,
    )


def get_rag_service(
    embedding_provider=Depends(get_embedding_provider),
    vector_repository: MongoVectorRepository = Depends(get_vector_repository),
    llm_provider=Depends(get_llm_provider),
) -> RAGService:
    return RAGService(embedding_provider, vector_repository, llm_provider)


def get_chat_service(
    conversation_repository: MongoConversationRepository = Depends(get_conversation_repository),
    rag_service: RAGService = Depends(get_rag_service),
) -> ChatService:
    return ChatService(conversation_repository, rag_service)


def get_ingestion_service(
    document_repository: MongoDocumentRepository = Depends(get_document_repository),
    embedding_provider=Depends(get_embedding_provider),
) -> IngestionService:
    return IngestionService(document_repository, embedding_provider)


def get_whatsapp_service(
    chat_service: ChatService = Depends(get_chat_service),
    messaging_provider: MetaWhatsAppProvider = Depends(get_messaging_provider),
    stt_provider=Depends(get_stt_provider),
    tts_provider=Depends(get_tts_provider),
) -> WhatsAppService:
    return WhatsAppService(chat_service, messaging_provider, stt_provider, tts_provider)
