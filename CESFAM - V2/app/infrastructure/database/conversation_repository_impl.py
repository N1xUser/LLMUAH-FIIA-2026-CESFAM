from datetime import datetime, timezone

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.domain.entities.conversation import Conversation
from app.domain.entities.message import Message
from app.domain.repositories.conversation_repository import ConversationRepository


class MongoConversationRepository(ConversationRepository):
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db["conversations"]

    async def get_or_create_by_external_id(self, external_user_id: str, channel: str) -> Conversation:
        raw = await self._collection.find_one({"external_user_id": external_user_id, "channel": channel})
        if raw is not None:
            raw["id"] = str(raw.pop("_id"))
            return Conversation(**raw)

        conversation = Conversation(channel=channel, external_user_id=external_user_id)
        data = conversation.model_dump(exclude={"id"})
        result = await self._collection.insert_one(data)
        conversation.id = str(result.inserted_id)
        return conversation

    async def add_message(self, conversation_id: str, message: Message) -> Conversation:
        await self._collection.update_one(
            {"_id": ObjectId(conversation_id)},
            {
                "$push": {"messages": message.model_dump()},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
        )
        raw = await self._collection.find_one({"_id": ObjectId(conversation_id)})
        raw["id"] = str(raw.pop("_id"))
        return Conversation(**raw)

    async def get_history(self, conversation_id: str, limit: int = 20) -> list[Message]:
        raw = await self._collection.find_one({"_id": ObjectId(conversation_id)})
        if raw is None:
            return []
        messages = [Message(**m) for m in raw.get("messages", [])]
        return messages[-limit:]
