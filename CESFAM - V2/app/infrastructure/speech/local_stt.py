import tempfile

from app.application.interfaces.speech_to_text_provider import SpeechToTextProvider


class LocalSpeechToTextProvider(SpeechToTextProvider):


    def __init__(self, model_size: str = "small") -> None:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise ImportError(
                "faster-whisper no está instalado. Ejecuta: "
                "pip install -r requirements-local.txt"
            ) from exc
        self._model = WhisperModel(model_size)

    async def transcribe(self, audio_bytes: bytes, mime_type: str) -> str:
        with tempfile.NamedTemporaryFile(suffix=".ogg") as tmp:
            tmp.write(audio_bytes)
            tmp.flush()
            segments, _ = self._model.transcribe(tmp.name)
            return " ".join(segment.text.strip() for segment in segments)
