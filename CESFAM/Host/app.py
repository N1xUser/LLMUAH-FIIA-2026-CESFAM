import os
import uuid
import json
import subprocess
import time
import secrets
import random
import sys

if os.name == 'nt':
    import msvcrt
else:
    import fcntl

from flask import Flask, request, jsonify, render_template, Response

app = Flask(__name__)
HISTORY_DIR = "history"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

if not os.path.exists(HISTORY_DIR):
    os.makedirs(HISTORY_DIR, exist_ok=True)
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)


class FileDict:
    """Dict-like object backed by a JSON file with file locking for multi-worker safety."""

    def __init__(self, filepath):
        self.filepath = filepath
        if not os.path.exists(filepath):
            with open(filepath, 'w') as f:
                json.dump({}, f)

    def _with_lock(self, callback):
        with open(self.filepath, 'r+') as f:
            if os.name == 'nt':
                pos = f.tell()
                f.seek(0)
                msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
                f.seek(pos)
            else:
                fcntl.flock(f, fcntl.LOCK_EX)
                
            try:
                try:
                    data = json.load(f)
                except (json.JSONDecodeError, ValueError):
                    data = {}
                result = callback(data)
                f.seek(0)
                f.truncate()
                json.dump(data, f)
                return result
            finally:
                if os.name == 'nt':
                    pos = f.tell()
                    f.seek(0)
                    msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                    f.seek(pos)
                else:
                    fcntl.flock(f, fcntl.LOCK_UN)

    def get(self, key, default=None):
        return self._with_lock(lambda d: d.get(key, default))

    def set(self, key, value):
        self._with_lock(lambda d: d.__setitem__(key, value))

    def delete(self, key):
        self._with_lock(lambda d: d.pop(key, None))

    def __contains__(self, key):
        return self._with_lock(lambda d: key in d)

    def cleanup_expired(self):
        now = time.time()
        def _cleanup(data):
            expired = [k for k, v in data.items() if isinstance(v, dict) and 'expires' in v and now > v['expires']]
            for k in expired:
                del data[k]
        self._with_lock(_cleanup)

    def verify_captcha(self, captcha_id, answer):
        def _verify(data):
            if captcha_id not in data:
                return None
            captcha_data = data[captcha_id]
            if time.time() > captcha_data['expires']:
                del data[captcha_id]
                return None
            try:
                if int(answer) == captcha_data['answer']:
                    del data[captcha_id]
                    token = secrets.token_hex(16)
                    return token
            except (ValueError, TypeError):
                pass
            del data[captcha_id]
            return None
        return self._with_lock(_verify)


CAPTCHAS = FileDict(os.path.join(DATA_DIR, "captchas.json"))
TOKENS = FileDict(os.path.join(DATA_DIR, "tokens.json"))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/captcha", methods=["GET"])
def get_captcha():
    a = random.randint(1, 10)
    b = random.randint(1, 10)
    captcha_id = str(uuid.uuid4())
    CAPTCHAS.set(captcha_id, {"answer": a + b, "expires": time.time() + 300})

    CAPTCHAS.cleanup_expired()

    return jsonify({"captcha_id": captcha_id, "text": f"¿Cuánto es {a} + {b}?"})

@app.route("/api/verify_captcha", methods=["POST"])
def verify_captcha():
    data = request.json
    if not data:
        return jsonify({"error": "Captcha incorrecto o expirado"}), 403

    captcha_id = data.get("captcha_id")
    answer = data.get("answer")

    token = CAPTCHAS.verify_captcha(captcha_id, answer)
    if token:
        TOKENS.set(token, time.time() + 1800)
        return jsonify({"token": token})

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

    token_expiry = TOKENS.get(token) if token else None
    if not token or token_expiry is None:
        return jsonify({"error": "Por favor, resuelve el captcha primero.", "needs_captcha": True}), 403

    if time.time() > token_expiry:
        TOKENS.delete(token)
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
    env["PYTHONUNBUFFERED"] = "1"
    
    def generate():
        yield f"data: {json.dumps({'chat_id': chat_id})}\n\n"
        
        process = subprocess.Popen(
            ["python", "-u", agent_script, query],
            cwd=agent_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            bufsize=1
        )
        
        full_response = []
        while True:
            char = process.stdout.read(1)
            if not char and process.poll() is not None:
                break
            if char:
                full_response.append(char)
                yield f"data: {json.dumps({'chunk': char})}\n\n"
                
        history.append({"role": "bot", "content": "".join(full_response)})
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
            
    return Response(generate(), mimetype="text/event-stream")

@app.route("/api/history/<chat_id>", methods=["GET"])
def get_history(chat_id):
    history_file = os.path.join(HISTORY_DIR, f"{chat_id}.json")
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    return jsonify([])

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5000)
