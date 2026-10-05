<div style="font-family: apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-weight: bold;">

# Generative AI RAG Service Backend

Este backend se encarga de servir las consultas y la conexión con WhatsApp, integrando el agente RAG local de la carpeta CESFAM. Además, provee una interfaz web responsiva segura para consultas manuales.

## Configuración

1. **RAGService**: El archivo `app/application/services/rag_service.py` ha sido modificado para instanciar y usar `RAGAgent` ubicado en `../../CESFAM/Model/Agent/Cloud/agent.py`.
2. **Conexión de WhatsApp**: El endpoint `POST /api/v1/whatsapp/webhook` (en el puerto 1218) recibe los mensajes de Meta, los procesa y pasa al `ChatService`.
3. **Interfaz Web**: Se incluye una interfaz web simple en la raíz (`GET /` en el puerto 1218) para interactuar directamente con el chatbot sin requerir la API Key de WhatsApp.
4. **Variables de entorno**: Es necesario definir las variables requeridas en `.env` (como las credenciales de Meta y la llave de Gemini ofuscada en partes `GEMINI_KEY_PART1` y `GEMINI_KEY_PART2`).

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

Para detener los servicios:

```bash
docker compose down
```

</div>
