from anthropic import AsyncAnthropic

from app.application.interfaces.llm_provider import LLMProvider
from app.domain.entities.message import Message, MessageRole


class ClaudeLLMProvider(LLMProvider):

    def __init__(self, api_key: str, model: str) -> None:
        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model

    async def generate(self, messages: list[Message], system_prompt: str | None = None) -> str:
        formatted = [
            {"role": "assistant" if m.role == MessageRole.ASSISTANT else "user", "content": m.content}
            for m in messages
            if m.role != MessageRole.SYSTEM
        ]
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=system_prompt or "",
            messages=formatted,
        )
        return "".join(block.text for block in response.content if block.type == "text")
