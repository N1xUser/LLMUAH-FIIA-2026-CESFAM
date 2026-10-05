from google import genai
from google.genai import types

from app.application.interfaces.text_to_speech_provider import TextToSpeechProvider


class GeminiTextToSpeechProvider(TextToSpeechProvider):

    mime_type = "audio/wav"

    def __init__(self, api_key: str, model: str, voice_name: str = "Kore") -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._voice_name = voice_name

    async def synthesize(self, text: str) -> bytes:
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=self._voice_name)
                    )
                ),
            ),
        )
        return response.candidates[0].content.parts[0].inline_data.data