from fastapi import APIRouter, Depends, UploadFile

from app.api.deps import get_chat_service, get_stt_provider
from app.api.v1.schemas.chat_schema import ChatRequest, ChatResponse
from app.application.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, chat_service: ChatService = Depends(get_chat_service)) -> ChatResponse:
    answer = await chat_service.send_message(
        external_user_id=request.user_id, channel="api", text=request.message
    )
    return ChatResponse(answer=answer)


@router.post("/audio", response_model=ChatResponse)
async def chat_with_audio(
    user_id: str,
    file: UploadFile,
    chat_service: ChatService = Depends(get_chat_service),
    stt_provider=Depends(get_stt_provider),
) -> ChatResponse:
    audio_bytes = await file.read()
    text = await stt_provider.transcribe(audio_bytes, file.content_type or "audio/ogg")
    answer = await chat_service.send_message(
        external_user_id=user_id, channel="api", text=text, was_audio=True
    )
    return ChatResponse(answer=answer)
