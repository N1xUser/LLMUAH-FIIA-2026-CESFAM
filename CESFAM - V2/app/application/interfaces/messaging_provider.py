from abc import ABC, abstractmethod


class MessagingProvider(ABC):

    @abstractmethod
    async def send_text(self, to: str, text: str) -> None: ...

    @abstractmethod
    async def send_audio(self, to: str, audio_bytes: bytes, mime_type: str) -> None: ...

    @abstractmethod
    async def download_media(self, media_id: str) -> tuple[bytes, str]: ...
