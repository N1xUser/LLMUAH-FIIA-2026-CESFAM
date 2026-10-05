import asyncio
import subprocess

from app.core.exceptions import ProviderError


async def to_whatsapp_ogg(audio_bytes: bytes) -> bytes:

    return await asyncio.to_thread(_convert_with_ffmpeg, audio_bytes)


def _convert_with_ffmpeg(audio_bytes: bytes) -> bytes:
    try:
        result = subprocess.run(
            ["ffmpeg", "-y", "-f", "wav", "-i", "pipe:0", "-c:a", "libopus", "-f", "ogg", "pipe:1"],
            input=audio_bytes,
            capture_output=True,
        )
    except FileNotFoundError as exc:
        raise ProviderError(
            "ffmpeg no está instalado (o no está en el PATH). Es necesario "
            "para convertir el audio generado a OGG/Opus, el único formato "
            "de audio que acepta WhatsApp para notas de voz."
        ) from exc

    if result.returncode != 0:
        raise ProviderError(
            "ffmpeg falló al convertir el audio a OGG/Opus: "
            f"{result.stderr.decode(errors='ignore')[-500:]}"
        )
    return result.stdout