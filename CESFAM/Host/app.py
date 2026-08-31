import os
import uuid
import json
import subprocess
import time
import secrets
import random
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)
HISTORY_DIR = "history"

CAPTCHAS = {}
TOKENS = {}

if not os.path.exists(HISTORY_DIR):
    os.makedirs(HISTORY_DIR)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/captcha", methods=["GET"])
def get_captcha():
    a = random.randint(1, 10)
    b = random.randint(1, 10)
    captcha_id = str(uuid.uuid4())
    CAPTCHAS[captcha_id] = {"answer": a + b, "expires": time.time() + 300}
    
    expired = [k for k, v in CAPTCHAS.items() if time.time() > v["expires"]]
    for k in expired:
        del CAPTCHAS[k]
        
    return jsonify({"captcha_id": captcha_id, "text": f"¿Cuánto es {a} + {b}?"})

@app.route("/api/verify_captcha", methods=["POST"])
def verify_captcha():
    data = request.json
    captcha_id = data.get("captcha_id")
    answer = data.get("answer")
    
    if captcha_id in CAPTCHAS:
        captcha_data = CAPTCHAS[captcha_id]
        if time.time() < captcha_data["expires"]:
            try:
                if int(answer) == captcha_data["answer"]:
                    token = secrets.token_hex(16)
                    TOKENS[token] = time.time() + 1800
                    del CAPTCHAS[captcha_id]
                    return jsonify({"token": token})
            except (ValueError, TypeError):
                pass
        del CAPTCHAS[captcha_id]
        
    return jsonify({"error": "Captcha incorrecto o expirado"}), 403


@app.route("/api/chats", methods=["GET"])
def get_chats():
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
    return jsonify(chats)

@app.route("/api/chat", methods=["POST"])
def chat():
    token = request.headers.get("Authorization")
    if token:
        token = token.replace("Bearer ", "")
        
    if not token or token not in TOKENS:
        return jsonify({"error": "Por favor, resuelve el captcha primero.", "needs_captcha": True}), 403
        
    if time.time() > TOKENS[token]:
        del TOKENS[token]
        return jsonify({"error": "Token expirado. Por favor, resuelve el captcha de nuevo.", "needs_captcha": True}), 403

    data = request.json
    chat_id = data.get("chat_id")
    query = data.get("query")
    
    if not chat_id:
        chat_id = str(uuid.uuid4())
        
    history_file = os.path.join(HISTORY_DIR, f"{chat_id}.json")
    history = []
    
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8") as f:
            history = json.load(f)
            
    history.append({"role": "user", "content": query})
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    agent_dir = os.path.join(base_dir, "..", "Model", "Agent", "Cloud")
    agent_script = os.path.join(agent_dir, "agent.py")
    
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    try:
        result = subprocess.run(
            ["python", agent_script, query],
            cwd=agent_dir,
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
            errors="replace",
            env=env
        )
        response_text = result.stdout
    except subprocess.CalledProcessError as e:
        response_text = str(e.stderr)
        
    history.append({"role": "bot", "content": response_text})
    
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
        
    return jsonify({"chat_id": chat_id, "response": response_text})

@app.route("/api/history/<chat_id>", methods=["GET"])
def get_history(chat_id):
    history_file = os.path.join(HISTORY_DIR, f"{chat_id}.json")
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    return jsonify([])

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5000)
