from google import genai
from google.genai import types

from app.application.interfaces.speech_to_text_provider import SpeechToTextProvider


class GeminiSpeechToTextProvider(SpeechToTextProvider):


    def __init__(self, api_key: str, model: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def transcribe(self, audio_bytes: bytes, mime_type: str) -> str:
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=[
                "Transcribe este audio de forma literal. Responde solo con "
                "el texto transcrito, sin comentarios ni introducciones.",
                types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
            ],
        )
        return (response.text or "").strip()
