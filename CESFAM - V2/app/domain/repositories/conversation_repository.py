from abc import ABC, abstractmethod

from app.domain.entities.conversation import Conversation
from app.domain.entities.message import Message


class ConversationRepository(ABC):
    @abstractmethod
    async def get_or_create_by_external_id(self, external_user_id: str, channel: str) -> Conversation: ...

    @abstractmethod
    async def add_message(self, conversation_id: str, message: Message) -> Conversation: ...

    @abstractmethod
    async def get_history(self, conversation_id: str, limit: int = 20) -> list[Message]: ...
