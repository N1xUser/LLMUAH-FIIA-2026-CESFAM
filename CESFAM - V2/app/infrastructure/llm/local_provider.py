import httpx

from app.application.interfaces.llm_provider import LLMProvider
from app.domain.entities.message import Message, MessageRole


class LocalLLMProvider(LLMProvider):


    def __init__(self, base_url: str, model: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model

    async def generate(self, messages: list[Message], system_prompt: str | None = None) -> str:
        payload_messages = []
        if system_prompt:
            payload_messages.append({"role": "system", "content": system_prompt})
        payload_messages += [
            {"role": "assistant" if m.role == MessageRole.ASSISTANT else "user", "content": m.content}
            for m in messages
            if m.role != MessageRole.SYSTEM
        ]

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self._base_url}/api/chat",
                json={"model": self._model, "messages": payload_messages, "stream": False},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("message", {}).get("content", "")
