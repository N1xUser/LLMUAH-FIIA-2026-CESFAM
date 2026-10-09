FROM python:3.12-slim

WORKDIR /workspace

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY ["CESFAM - V2/requirements.txt", "./requirements.txt"]
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir google-genai numpy python-dotenv

COPY ["CESFAM - V2", "./CESFAM - V2"]
COPY ["CESFAM - Pipeline", "./CESFAM - Pipeline"]

WORKDIR "/workspace/CESFAM - V2"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
