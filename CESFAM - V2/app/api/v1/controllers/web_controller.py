import os
import json
import uuid
import time
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
from app.api.deps import get_rag_service

router = APIRouter(prefix="/web", tags=["web"])

HISTORY_DIR = "app/history"
if not os.path.exists(HISTORY_DIR):
    os.makedirs(HISTORY_DIR, exist_ok=True)

class ChatRequest(BaseModel):
    query: str
    chat_id: str | None = None

@router.get("/chats")
async def get_chats():
    chats = []
    if os.path.exists(HISTORY_DIR):
        for filename in os.listdir(HISTORY_DIR):
            if filename.endswith(".json"):
                chat_id = filename[:-5]
                filepath = os.path.join(HISTORY_DIR, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        history = json.load(f)
                        title = "Nuevo chat"
                        for msg in history:
                            if msg.get("role") == "user":
                                title = msg.get("content", "")[:30]
                                if len(msg.get("content", "")) > 30:
                                    title += "..."
                                break
                        modified_time = os.path.getmtime(filepath)
                        chats.append({"id": chat_id, "title": title, "updated": modified_time})
                except Exception:
                    pass
    chats.sort(key=lambda x: x["updated"], reverse=True)
    return chats

@router.get("/history/{chat_id}")
async def get_history(chat_id: str):
    history_file = os.path.join(HISTORY_DIR, f"{chat_id}.json")
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

class CaptchaVerify(BaseModel):
    captcha_id: str
    answer: str

import random
import secrets

CAPTCHAS_FILE = os.path.join(HISTORY_DIR, "captchas.json")
TOKENS_FILE = os.path.join(HISTORY_DIR, "tokens.json")

def _load_json(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            try:
                return json.load(f)
            except:
                pass
    return {}

def _save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

@router.get("/captcha")
async def get_captcha():
    a = random.randint(1, 10)
    b = random.randint(1, 10)
    captcha_id = str(uuid.uuid4())
    
    captchas = _load_json(CAPTCHAS_FILE)
    captchas[captcha_id] = {"answer": a + b, "expires": time.time() + 300}
    
    now = time.time()
    captchas = {k: v for k, v in captchas.items() if v.get("expires", 0) > now}
    _save_json(CAPTCHAS_FILE, captchas)
    
    return {"captcha_id": captcha_id, "text": f"¿Cuánto es {a} + {b}?"}

@router.post("/verify_captcha")
async def verify_captcha(data: CaptchaVerify):
    captchas = _load_json(CAPTCHAS_FILE)
    if data.captcha_id not in captchas:
        raise HTTPException(status_code=403, detail="Captcha incorrecto o expirado")
    
    captcha_data = captchas[data.captcha_id]
    if time.time() > captcha_data.get("expires", 0):
        del captchas[data.captcha_id]
        _save_json(CAPTCHAS_FILE, captchas)
        raise HTTPException(status_code=403, detail="Captcha incorrecto o expirado")
        
    try:
        if int(data.answer) == captcha_data["answer"]:
            del captchas[data.captcha_id]
            token = secrets.token_hex(16)
            tokens = _load_json(TOKENS_FILE)
            tokens[token] = time.time() + 1800
            _save_json(CAPTCHAS_FILE, captchas)
            _save_json(TOKENS_FILE, tokens)
            return {"token": token}
    except ValueError:
        pass
        
    del captchas[data.captcha_id]
    _save_json(CAPTCHAS_FILE, captchas)
    raise HTTPException(status_code=403, detail="Captcha incorrecto o expirado")


@router.post("/chat")
async def web_chat(request: Request):
    token = request.headers.get("Authorization")
    if token:
        token = token.replace("Bearer ", "")
        
    tokens = _load_json(TOKENS_FILE)
    token_expiry = tokens.get(token)
    
    if not token or token_expiry is None:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=403, content={"error": "Por favor, resuelve el captcha primero.", "needs_captcha": True})
        
    if time.time() > token_expiry:
        del tokens[token]
        _save_json(TOKENS_FILE, tokens)
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=403, content={"error": "Token expirado. Por favor, resuelve el captcha de nuevo.", "needs_captcha": True})

    data = await request.json()
    chat_id = data.get("chat_id")
    query = data.get("query")
    
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    if not chat_id:
        chat_id = str(uuid.uuid4())
        
    history_file = os.path.join(HISTORY_DIR, f"{chat_id}.json")
    history = []
    
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8") as f:
            history = json.load(f)
            
    history.append({"role": "user", "content": query})
    
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    async def event_generator():
        yield f"data: {json.dumps({'chat_id': chat_id})}\n\n"
        
        from app.application.services.rag_service import RAGAgent
        if RAGAgent:
            agent = RAGAgent()
            answer_generator, _ = agent.query(query, top_k=5)
            full_response = []
            for chunk in answer_generator:
                full_response.append(chunk)
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                await asyncio.sleep(0.01) 
                
            history.append({"role": "bot", "content": "".join(full_response)})
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        else:
            yield f"data: {json.dumps({'chunk': 'Agente no disponible.'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
