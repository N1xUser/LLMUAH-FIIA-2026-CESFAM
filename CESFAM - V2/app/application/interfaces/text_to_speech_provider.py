from abc import ABC, abstractmethod


class TextToSpeechProvider(ABC):

    mime_type: str = "audio/ogg"

    @abstractmethod
    async def synthesize(self, text: str) -> bytes: ...
