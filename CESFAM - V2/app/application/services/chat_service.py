from app.application.services.rag_service import RAGService
from app.domain.entities.message import Message, MessageRole
from app.domain.repositories.conversation_repository import ConversationRepository


class ChatService:

    def __init__(self, conversation_repository: ConversationRepository, rag_service: RAGService) -> None:
        self._conversations = conversation_repository
        self._rag = rag_service

    async def send_message(
        self, external_user_id: str, channel: str, text: str, was_audio: bool = False
    ) -> str:
        conversation = await self._conversations.get_or_create_by_external_id(external_user_id, channel)
        await self._conversations.add_message(
            conversation.id, Message(role=MessageRole.USER, content=text, was_audio=was_audio)
        )
        history = await self._conversations.get_history(conversation.id)
        answer = await self._rag.answer(text, history[:-1])
        await self._conversations.add_message(
            conversation.id, Message(role=MessageRole.ASSISTANT, content=answer)
        )
        return answer
