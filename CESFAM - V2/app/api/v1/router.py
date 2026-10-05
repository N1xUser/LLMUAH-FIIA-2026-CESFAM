from fastapi import APIRouter

from app.api.v1.controllers import chat_controller, documents_controller, whatsapp_controller, web_controller

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(chat_controller.router)
api_router.include_router(documents_controller.router)
api_router.include_router(whatsapp_controller.router)
api_router.include_router(web_controller.router)
