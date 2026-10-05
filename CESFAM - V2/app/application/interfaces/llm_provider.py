from abc import ABC, abstractmethod

from app.domain.entities.message import Message


class LLMProvider(ABC):

    @abstractmethod
    async def generate(self, messages: list[Message], system_prompt: str | None = None) -> str: ...
