import hashlib
import hmac
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query, Request

from app.api.deps import get_whatsapp_service
from app.application.services.whatsapp_service import WhatsAppService
from app.core.config import Settings, get_settings

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])
logger = logging.getLogger(__name__)


def _has_valid_signature(raw_body: bytes, signature_header: str | None, app_secret: str) -> bool:
    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected_signature = hmac.new(app_secret.encode(), raw_body, hashlib.sha256).hexdigest()
    received_signature = signature_header.removeprefix("sha256=")

    return hmac.compare_digest(expected_signature, received_signature)


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
    settings: Settings = Depends(get_settings),
):
    if hub_mode == "subscribe" and hub_verify_token == settings.meta_verify_token:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Token de verificación inválido")


@router.post("/webhook")
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    whatsapp_service: WhatsAppService = Depends(get_whatsapp_service),
    settings: Settings = Depends(get_settings),
    x_hub_signature_256: str | None = Header(default=None),
):
    raw_body = await request.body()

    if settings.meta_app_secret:
        if not _has_valid_signature(raw_body, x_hub_signature_256, settings.meta_app_secret):
            raise HTTPException(status_code=403, detail="Firma de webhook inválida")
    else:
        logger.warning(
            "META_APP_SECRET no está configurado: el webhook está aceptando "
            "peticiones sin validar su firma. No lo dejes así en producción."
        )

    payload = await request.json()
    background_tasks.add_task(whatsapp_service.handle_webhook_payload, payload)
    return {"status": "received"}