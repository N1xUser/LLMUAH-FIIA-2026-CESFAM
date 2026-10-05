from google import genai
from google.genai import types

from app.application.interfaces.llm_provider import LLMProvider
from app.domain.entities.message import Message, MessageRole


class GeminiLLMProvider(LLMProvider):


    def __init__(self, api_key: str, model: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def generate(self, messages: list[Message], system_prompt: str | None = None) -> str:
        contents = [
            types.Content(
                role="model" if m.role == MessageRole.ASSISTANT else "user",
                parts=[types.Part.from_text(text=m.content)],
            )
            for m in messages
            if m.role != MessageRole.SYSTEM
        ]
        config = types.GenerateContentConfig(system_instruction=system_prompt) if system_prompt else None

        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=contents,
            config=config,
        )
        return response.text or ""
