import io

from app.application.interfaces.text_to_speech_provider import TextToSpeechProvider


class LocalTextToSpeechProvider(TextToSpeechProvider):

    mime_type = "audio/mpeg"

    def __init__(self, lang: str = "es") -> None:
        try:
            import gtts  
        except ImportError as exc:
            raise ImportError(
                "gTTS no está instalado. Ejecuta: pip install -r requirements-local.txt"
            ) from exc
        self._lang = lang

    async def synthesize(self, text: str) -> bytes:
        from gtts import gTTS

        buffer = io.BytesIO()
        gTTS(text=text, lang=self._lang).write_to_fp(buffer)
        return buffer.getvalue()
