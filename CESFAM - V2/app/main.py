from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from app.api.middleware.error_handler import register_exception_handlers
from app.api.v1.router import api_router
from app.api.v1.controllers.whatsapp_controller import verify_webhook, receive_webhook
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.infrastructure.database.mongo_client import close_mongo_connection, connect_to_mongo


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging()
    await connect_to_mongo(settings.mongo_uri, settings.mongo_db_name)
    yield
    await close_mongo_connection()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Servicio de IA Generativa (RAG) agnóstico al modelo",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(api_router)
    
    # Rutas para soportar el Webhook expuesto directamente en la raíz (/webhook)
    app.get("/webhook")(verify_webhook)
    app.post("/webhook")(receive_webhook)
    
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def get_web_chat():
        with open("app/static/index.html", "r", encoding="utf-8") as f:
            return f.read()
            
    return app


app = create_app()
