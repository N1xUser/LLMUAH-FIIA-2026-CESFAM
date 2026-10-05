from typing import Any

from app.application.interfaces.messaging_provider import MessagingProvider
from app.application.interfaces.speech_to_text_provider import SpeechToTextProvider
from app.application.interfaces.text_to_speech_provider import TextToSpeechProvider
from app.application.services.chat_service import ChatService
from app.infrastructure.messaging.audio_conversion import to_whatsapp_ogg
from app.infrastructure.messaging.text_formatting import format_for_whatsapp, strip_markdown


class WhatsAppService:

    def __init__(
        self,
        chat_service: ChatService,
        messaging_provider: MessagingProvider,
        stt_provider: SpeechToTextProvider,
        tts_provider: TextToSpeechProvider,
    ) -> None:
        self._chat = chat_service
        self._messaging = messaging_provider
        self._stt = stt_provider
        self._tts = tts_provider

    async def handle_webhook_payload(self, payload: dict[str, Any]) -> None:
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for message in value.get("messages", []):
                    await self._handle_message(message)

    async def _handle_message(self, message: dict[str, Any]) -> None:
        from_number = message["from"]
        message_type = message.get("type")

        was_audio = message_type == "audio"
        if message_type == "text":
            text = message["text"]["body"]
        elif message_type == "audio":
            media_id = message["audio"]["id"]
            audio_bytes, mime_type = await self._messaging.download_media(media_id)
            text = await self._stt.transcribe(audio_bytes, mime_type)
        else:
            await self._messaging.send_text(
                from_number, "Por ahora solo puedo procesar mensajes de texto o audio."
            )
            return

        answer = await self._chat.send_message(
            external_user_id=from_number, channel="whatsapp", text=text, was_audio=was_audio
        )

        await self._messaging.send_text(from_number, format_for_whatsapp(answer))
        if was_audio:
            audio_reply = await self._tts.synthesize(strip_markdown(answer))
            ogg_audio = await to_whatsapp_ogg(audio_reply)
            await self._messaging.send_audio(from_number, ogg_audio, "audio/ogg; codecs=opus")