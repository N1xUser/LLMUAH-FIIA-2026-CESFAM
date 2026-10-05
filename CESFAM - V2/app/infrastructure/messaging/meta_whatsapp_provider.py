import logging

import httpx

from app.application.interfaces.messaging_provider import MessagingProvider

logger = logging.getLogger(__name__)


class MetaWhatsAppProvider(MessagingProvider):


    def __init__(self, access_token: str, phone_number_id: str, api_version: str = "v20.0") -> None:
        self._token = access_token
        self._phone_number_id = phone_number_id
        self._base_url = f"https://graph.facebook.com/{api_version}"

    @property
    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}

    @staticmethod
    def _raise_with_details(resp: httpx.Response) -> None:
  
        if resp.is_error:
            logger.warning("Meta respondió %s: %s", resp.status_code, resp.text)
        resp.raise_for_status()

    async def send_text(self, to: str, text: str) -> None:
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text},
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self._base_url}/{self._phone_number_id}/messages",
                headers=self._headers,
                json=payload,
            )
            self._raise_with_details(resp)

    async def send_audio(self, to: str, audio_bytes: bytes, mime_type: str) -> None:
        media_id = await self._upload_media(audio_bytes, mime_type)
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "audio",
            "audio": {"id": media_id},
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self._base_url}/{self._phone_number_id}/messages",
                headers=self._headers,
                json=payload,
            )
            self._raise_with_details(resp)

    async def _upload_media(self, audio_bytes: bytes, mime_type: str) -> str:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self._base_url}/{self._phone_number_id}/media",
                headers=self._headers,
                data={"messaging_product": "whatsapp", "type": mime_type},
                files={"file": ("audio", audio_bytes, mime_type)},
            )
            self._raise_with_details(resp)
            return resp.json()["id"]

    async def download_media(self, media_id: str) -> tuple[bytes, str]:
        async with httpx.AsyncClient(timeout=30) as client:
            meta_resp = await client.get(f"{self._base_url}/{media_id}", headers=self._headers)
            self._raise_with_details(meta_resp)
            meta = meta_resp.json()
            media_url = meta["url"]
            mime_type = meta.get("mime_type", "audio/ogg")

            file_resp = await client.get(media_url, headers=self._headers)
            self._raise_with_details(file_resp)
            return file_resp.content, mime_type