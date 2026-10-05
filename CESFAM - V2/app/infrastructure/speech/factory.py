from app.application.interfaces.speech_to_text_provider import SpeechToTextProvider
from app.application.interfaces.text_to_speech_provider import TextToSpeechProvider
from app.core.config import Settings
from app.infrastructure.speech.gemini_stt import GeminiSpeechToTextProvider
from app.infrastructure.speech.gemini_tts import GeminiTextToSpeechProvider
from app.infrastructure.speech.local_stt import LocalSpeechToTextProvider
from app.infrastructure.speech.local_tts import LocalTextToSpeechProvider


def build_stt_provider(settings: Settings) -> SpeechToTextProvider:
    if settings.stt_provider == "local":
        return LocalSpeechToTextProvider()
    return GeminiSpeechToTextProvider(api_key=settings.gemini_api_key, model=settings.gemini_model)


def build_tts_provider(settings: Settings) -> TextToSpeechProvider:
    if settings.tts_provider == "local":
        return LocalTextToSpeechProvider()
    return GeminiTextToSpeechProvider(api_key=settings.gemini_api_key, model=settings.gemini_tts_model)
