<div style="font-family: apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-weight: bold;">

# Generative AI RAG Service Backend

La guía completa para desplegar el chatbot en WhatsApp con Docker, ngrok y Meta,
incluyendo pruebas y diagnóstico, está en el [README principal](../README.md).

Este backend se encarga de servir las consultas y la conexión con WhatsApp, integrando el agente RAG local de la carpeta CESFAM. Además, provee una interfaz web responsiva segura para consultas manuales.

## Configuración

1. **RAGService**: El archivo `app/application/services/rag_service.py` ha sido modificado para instanciar y usar `RAGAgent` ubicado en `../../CESFAM/Model/Agent/Cloud/agent.py`.
2. **Conexión de WhatsApp**: El endpoint `POST /api/v1/whatsapp/webhook` recibe los mensajes de Meta, los procesa y pasa al `ChatService`. Alternativamente, también se ha expuesto en la raíz `/webhook`.
3. **Interfaz Web**: Se incluye una interfaz web simple en la raíz (`GET /` en el puerto 1218) para interactuar directamente con el chatbot sin requerir la API Key de WhatsApp.
4. **Variables de entorno**: Las credenciales requeridas han sido configuradas en el archivo `.env`, incluyendo `META_ACCESS_TOKEN`, `META_PHONE_NUMBER_ID`, `META_WHATSAPP_BUSINESS_ACCOUNT_ID`, `META_VERIFY_TOKEN` (seteado a `mi_token_secreto_123`) y `GEMINI_API_KEY`.

## Reglas del Agente (System Prompt)

El system prompt del agente (definido en `CESFAM - Pipeline/Model/Agent/Cloud/llm_service.py`) implementa las siguientes capas de proteccion:

1. **Identidad**: Asistente de Salud Intercultural CESFAM, orientado al Decreto 21 (Art. 7, Ley 20.584).
2. **Alcance tematico estricto**: Solo responde sobre salud publica, CESFAM, interculturalidad, normativa MINSAL, sistemas medicos indigenas, GES/AUGE, facilitadores interculturales, y derechos de pacientes.
3. **Reglas de rechazo**: Cualquier pregunta fuera de ambito recibe un mensaje estandar de redireccion a temas de salud.
4. **Proteccion anti-prompt-injection**: Rechaza intentos de jailbreak, cambio de rol, DAN, "modo desarrollador", "olvida tus instrucciones", roleplay externo, y cualquier variante de manipulacion. No revela el system prompt bajo ninguna circunstancia.
5. **Tono**: Espanol chileno, cercano, respetuoso y profesional. Cita fuentes normativas cuando corresponde.

## Ejecución Local

Para ejecutar el chatbot de forma local usando Python, ejecuta:
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Recuerda configurar la URL del webhook en Meta como `https://<tu-url-de-ngrok>/api/v1/whatsapp/webhook` con el token `mi_token_secreto_123`.

## Despliegue en Servidor

Para desplegar este proyecto en tu servidor (VPS, AWS, DigitalOcean, etc.), sigue estos pasos:

1. Copia toda la carpeta del proyecto (incluyendo `CESFAM` y `generative-ai-rag-service`) a tu servidor.
2. Asegúrate de tener instalado **Docker** y **Docker Compose** en tu servidor.
3. Configura correctamente el archivo `.env` en tu servidor con tus credenciales y llaves.
4. Levanta el servicio ejecutando el siguiente comando en la carpeta `generative-ai-rag-service`:

```bash
docker compose up -d --build
```

Esto levantará los siguientes servicios:
- **API (WhatsApp y Web)**: http://tu-ip-de-servidor:1218
- **MongoDB**: (uso interno de base de datos)

Docker Compose configura `MONGO_URI=mongodb://mongo:27017` para usar el servicio
MongoDB incluido. WhatsApp necesita esta conexión para guardar conversaciones;
la interfaz web guarda su historial en archivos. Una URI de Atlas de ejemplo en
`.env` puede hacer que WhatsApp falle aunque la web responda correctamente.

El túnel de WhatsApp debe apuntar al puerto **1218** de esta misma API. Comprueba
que `META_PHONE_NUMBER_ID` corresponda al número al que escriben los usuarios y
que la URL pública configurada en Meta termine en `/webhook` o
`/api/v1/whatsapp/webhook`. Si el túnel se detiene, Meta no podrá entregar mensajes
al contenedor local.

Para detener los servicios:

```bash
docker compose down
```

</div>
