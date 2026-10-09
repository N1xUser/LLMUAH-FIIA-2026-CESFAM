# CESFAM Chatbot: despliegue en WhatsApp

Guía para ejecutar el chatbot localmente con Docker y conectarlo a WhatsApp Cloud API mediante ngrok. Los valores entre `<...>` son ejemplos y deben reemplazarse. Esta guía no contiene credenciales reales.

Para instalar desde cero en Windows, sigue la [guía de instalación](instalación.md).

## 1. Arquitectura

```text
WhatsApp del usuario
  -> Meta WhatsApp Cloud API
  -> ngrok: URL HTTPS pública /webhook
  -> Puerto 1218 del PC que ejecuta Docker
  -> FastAPI -> MongoDB -> agente RAG
  -> API de mensajes de Meta -> respuesta en WhatsApp
```

- `CESFAM - V2/`: backend FastAPI, web, integración WhatsApp y Docker.
- `CESFAM - Pipeline/Model/Agent/Cloud/`: agente RAG y servicio Gemini.
- `CESFAM - Pipeline/Model/Agent/Cloud/Process/`: conocimiento en Markdown; `contex.md` aporta contexto al agente.
- `CESFAM - Pipeline/Model/Agent/Cloud/cache/embeddings_store.pkl`: caché de embeddings.

El asistente orienta sobre salud e interculturalidad según sus documentos y las reglas de `llm_service.py`.

| Recurso | Dirección o función |
| --- | --- |
| Web local | `http://localhost:1218/` |
| Documentación API | `http://localhost:1218/docs` |
| Puerto adicional de la misma API | `1219` |
| Puerto interno del contenedor API | `8000` |
| Webhook | `/webhook` o `/api/v1/whatsapp/webhook` |
| GET del webhook | Verifica token y devuelve el challenge de Meta |
| POST del webhook | Recibe mensajes y programa su procesamiento |
| MongoDB dentro de Docker | `mongodb://mongo:27017` |
| Inspector ngrok | `http://127.0.0.1:4040` |

Un Flask con solo `GET /webhook` verifica la URL, pero no procesa mensajes. Este proyecto ya implementa GET, POST y el envío de respuestas.

## 2. Requisitos

1. Docker Desktop iniciado, con Docker Compose disponible.
2. Repositorio completo con ambas carpetas principales.
3. Aplicación de Meta con WhatsApp Cloud API y acceso a la cuenta de WhatsApp Business, denominada WABA.
4. Número habilitado para Cloud API, sus identificadores y token con acceso a esos activos.
5. API key de Gemini con acceso a los modelos utilizados.
6. ngrok instalado y autenticado.
7. Internet y un computador encendido durante la operación.

Los comandos usan PowerShell. Comienza en la raíz del repositorio.

## 3. Credenciales y número correcto

Obtén los siguientes datos en Meta Developers o WhatsApp Manager para la misma aplicación, WABA y número:

| Variable | Contenido |
| --- | --- |
| `META_ACCESS_TOKEN` | Token para Graph API y envío de mensajes |
| `META_PHONE_NUMBER_ID` | Identificador del número del bot, no el teléfono con `+56` |
| `META_WHATSAPP_BUSINESS_ACCOUNT_ID` | Identificador de la WABA propietaria |
| `META_VERIFY_TOKEN` | Texto secreto elegido por ti, idéntico en Meta y en el backend |
| `META_APP_SECRET` | Secreto de la aplicación Meta para validar firmas de POST |
| `META_API_VERSION` | Versión de Graph API compatible y vigente |
| `GEMINI_API_KEY` | API key del agente |

El authtoken de ngrok, el token de verificación, el access token de Meta y el secreto de la aplicación son distintos.

El envío de mensajes necesita `whatsapp_business_messaging`; administrar suscripciones de WABA necesita `whatsapp_business_management`. El token debe tener además acceso a los activos correspondientes. Consulta las referencias oficiales al final para los requisitos de tu modalidad de cuenta.

Si usas un número de prueba, comprueba en Meta los destinatarios permitidos. Para uso permanente, configura un token de usuario del sistema con los permisos y activos necesarios, y revisa su caducidad.

### Verificar el teléfono asociado

Consulta Graph API con una herramienta que mantenga las credenciales fuera de archivos compartidos:

```text
GET https://graph.facebook.com/<VERSION>/<ID_NUMERO>?fields=id,display_phone_number
GET https://graph.facebook.com/<VERSION>/<ID_WABA>/phone_numbers?fields=id,display_phone_number
Authorization: Bearer <META_ACCESS_TOKEN>
```

El `display_phone_number` debe coincidir con el teléfono al que escribes en WhatsApp. Si no coincide, ese chat pertenece a otra integración aunque el webhook esté verificado.

## 4. Configurar .env

Si todavía no existe el archivo:

```powershell
Copy-Item 'CESFAM - V2/.env.example' 'CESFAM - V2/.env'
```

Si ya existe, edítalo sin sobrescribir sus credenciales. Completa como mínimo:

```dotenv
GEMINI_API_KEY=<API_KEY_GEMINI>
META_ACCESS_TOKEN=<ACCESS_TOKEN_META>
META_PHONE_NUMBER_ID=<ID_NUMERO_BOT>
META_WHATSAPP_BUSINESS_ACCOUNT_ID=<ID_WABA>
META_VERIFY_TOKEN=<TOKEN_VERIFICACION_ELEGIDO>
META_APP_SECRET=<SECRETO_APLICACION_META>
META_API_VERSION=<VERSION_GRAPH_API>
MONGO_DB_NAME=generative_rag
```

`META_APP_SECRET` es reconocido aunque no esté en `.env.example`. Configúralo para validar `X-Hub-Signature-256` en los POST. Cuando está vacío, el código acepta peticiones sin firma y registra una advertencia; no dejes esa configuración en producción.

El Compose actual impone `MONGO_URI=mongodb://mongo:27017` y `VECTOR_SEARCH_BACKEND=local` por encima de `.env`. Esto utiliza el MongoDB incluido y evita la URI de Atlas de ejemplo. Para usar Atlas, modifica explícitamente esas entradas y configura una instancia real.

El flujo actual usa el `RAGAgent` del Pipeline. Sus modelos de embeddings y generación están definidos en `CESFAM - Pipeline/Model/Agent/Cloud/llm_service.py`: cambiar solamente `GEMINI_MODEL` o `GEMINI_EMBEDDING_MODEL` no modifica esos modelos del agente. Revisa allí su disponibilidad para tu cuenta. Si existen `GEMINI_KEY_PART1` y `GEMINI_KEY_PART2`, ambas tienen prioridad sobre la API key directa.

No publiques tokens en Git, capturas o documentación. Aunque Git excluye `.env`, el Dockerfile copia carpetas completas: antes de distribuir imágenes, excluye los `.env` mediante `.dockerignore` y proporciona las credenciales en tiempo de ejecución.

## 5. Iniciar Docker

```powershell
Set-Location 'CESFAM - V2'
docker compose up -d --build
docker compose ps
```

`api` y `mongo` deben estar en ejecución. Comprueba la web:

```powershell
(Invoke-WebRequest 'http://localhost:1218/' -UseBasicParsing).StatusCode
```

Resultado esperado: `200`. Abre la web y prueba un saludo y una consulta del ámbito del chatbot. Observa los registros con:

```powershell
docker compose logs -f api
```

La web guarda su historial en archivos; WhatsApp lo guarda en MongoDB. Que la web funcione no confirma que el flujo de WhatsApp funcione.

## 6. Instalar y autenticar ngrok

Sigue la [guía oficial para Windows](https://ngrok.com/download/windows). Una opción de instalación es:

```powershell
winget install ngrok -s msstore
```

Abre una nueva terminal si ngrok no aparece en el PATH. Obtén tu authtoken en el panel de ngrok y configúralo localmente:

```powershell
ngrok config add-authtoken '<AUTHTOKEN_NGROK>'
ngrok config check
```

En el equipo preparado durante este despliegue también existe una instalación independiente en `%LOCALAPPDATA%\CESFAM-tools\ngrok\ngrok.exe`. Puedes invocarla así:

```powershell
& "$env:LOCALAPPDATA\CESFAM-tools\ngrok\ngrok.exe" config check
```

## 7. Publicar el puerto correcto

Ejecuta en el mismo PC que Docker:

```powershell
ngrok http 1218
```

Si tu cuenta tiene un dominio asignado:

```powershell
ngrok http 1218 --url https://<TU_DOMINIO>.ngrok-free.dev
```

Para la instalación independiente, sustituye `ngrok` por `& "$env:LOCALAPPDATA\CESFAM-tools\ngrok\ngrok.exe"`.

La salida debe reenviar la URL HTTPS a `http://localhost:1218`. Mantén ngrok activo. Comprueba la URL pública:

```powershell
Invoke-WebRequest 'https://<TU_DOMINIO>.ngrok-free.dev/openapi.json' `
  -Headers @{'ngrok-skip-browser-warning'='1'} -UseBasicParsing
```

Debe responder `200` con la definición de FastAPI. La URL del webhook será:

```text
https://<TU_DOMINIO>.ngrok-free.dev/webhook
```

### Si ngrok está en el PC de un colega

`localhost` siempre corresponde al PC donde se ejecuta el comando. `ngrok http 80` en el computador del colega publica su puerto 80, no tu Docker.

Lo recomendado para estas pruebas es ngrok junto a Docker. Si ambos equipos tienen conectividad entre sí, el colega puede apuntar a tu PC:

```powershell
ngrok http http://<IP_DEL_PC_DOCKER>:1218
```

Comprueba primero desde su PC que abre `http://<IP_DEL_PC_DOCKER>:1218/`. En redes diferentes esa IP puede no ser accesible; utiliza ngrok en el PC de Docker o una conexión de red previamente habilitada.

## 8. Configurar Meta y suscribir mensajes

En Meta Developers, abre la configuración de WhatsApp o Webhooks para `whatsapp_business_account`:

1. Configura la URL pública completa terminada en `/webhook`.
2. Introduce el mismo valor de `META_VERIFY_TOKEN` que tiene el contenedor.
3. Verifica y guarda; el backend debe recibir GET y responder `200` con el challenge.
4. Suscribe el campo `messages`.
5. Confirma que la aplicación está suscrita a la WABA correcta y que el número pertenece a esa WABA.

La ubicación de estas opciones puede cambiar en el panel. El resultado requerido es una suscripción activa a `messages` con entrega a la URL HTTPS del backend.

### Configuración por Graph API

Usa la versión definida en `META_API_VERSION` y `Authorization: Bearer <META_ACCESS_TOKEN>`.

Para suscribir la aplicación a la WABA:

```text
POST https://graph.facebook.com/<VERSION>/<ID_WABA>/subscribed_apps
```

Para configurar una URL alternativa por WABA, una vez suscrita la aplicación:

```http
POST https://graph.facebook.com/<VERSION>/<ID_WABA>/subscribed_apps
Authorization: Bearer <META_ACCESS_TOKEN>
Content-Type: application/json

{
  "override_callback_uri": "https://<TU_DOMINIO>.ngrok-free.dev/webhook",
  "verify_token": "<MISMO_META_VERIFY_TOKEN>"
}
```

Meta verifica el endpoint. El resultado esperado es `{"success": true}`. Comprueba lo guardado:

```text
GET https://graph.facebook.com/<VERSION>/<ID_WABA>/subscribed_apps
GET https://graph.facebook.com/<VERSION>/<ID_NUMERO>?fields=id,display_phone_number,webhook_configuration
```

La suscripción debe mostrar `override_callback_uri` con la URL esperada. La alternativa por WABA puede coexistir con la URL general anterior de la aplicación; revisa la configuración efectiva del número. No sustituye la suscripción al campo `messages`.

## 9. Prueba completa

1. Mantén Docker y ngrok activos.
2. Desde otro WhatsApp, escribe al `display_phone_number` confirmado por Meta.
3. Envía `Hola` y después `¿Qué es un facilitador intercultural?`.
4. Comprueba en los logs `POST /webhook` o `POST /api/v1/whatsapp/webhook`.
5. Comprueba respuestas adecuadas y distintas para ambas consultas.
6. Si hay POST `200` sin respuesta, revisa también errores posteriores del procesamiento en segundo plano.

Los GET solo prueban la verificación de la URL. No prueban mensajes entrantes, acceso al modelo ni envío. Los eventos de estado también pueden producir POST sin contener un mensaje del usuario.

Este bot responde con texto libre a mensajes recibidos; no implementa campañas ni envío de plantillas. Para contactar fuera de la ventana de atención de WhatsApp, diseña ese flujo según las reglas vigentes de Meta.

## 10. Audio

El código contempla transcripción, respuesta de texto y síntesis de voz. Necesita modelos STT/TTS disponibles y `ffmpeg` con `libopus` para convertir el audio a OGG/Opus.

El Dockerfile actual no instala `ffmpeg`. Para habilitar notas de voz, agrega después de `FROM`:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*
```

Reconstruye y comprueba:

```powershell
docker compose up -d --build
docker compose exec api ffmpeg -version
```

Revisa `STT_PROVIDER`, `TTS_PROVIDER`, `GEMINI_MODEL` y `GEMINI_TTS_MODEL`. Prueba texto antes de audio.

## 11. Diagnóstico

| Síntoma | Qué comprobar |
| --- | --- |
| Respuesta antigua repetida | Número del chat y si este contenedor recibe su POST; puede responder otra aplicación |
| Web funciona, WhatsApp falla | MongoDB, credenciales Meta, webhook y errores del procesamiento |
| Solo GET en Docker | Número, suscripción `messages`, aplicación suscrita a WABA y URL efectiva |
| `404` en `/openapi.json` público | Túnel apuntando a otro servidor o puerto |
| `ERR_NGROK_4018` | Falta authtoken válido de ngrok |
| ngrok rechaza el dominio | Dominio asignado a tu cuenta y ausencia de otro endpoint incompatible |
| GET de verificación `403` | Token idéntico y `hub.mode=subscribe` |
| Abrir `/webhook` directamente da `422` | Faltan `hub.mode`, `hub.verify_token` y `hub.challenge`; no es una prueba de verificación |
| POST `403` | Secreto de aplicación y firma enviada por Meta |
| POST `200` sin respuesta | Errores posteriores de MongoDB, Gemini o envío a Meta |
| Token de Meta vencido o sin permisos | Renovación, permisos y acceso a activos |
| Error de MongoDB | Hostname `mongo` dentro del contenedor; no usar Atlas de ejemplo |
| Error del modelo | API key, disponibilidad de modelos y cuotas de Gemini |
| Audio falla | `ffmpeg`, modelos y configuración STT/TTS |
| Código editado no cambia al reiniciar | Reconstruir imagen; el código no está montado como volumen |

## 12. Actualizar, detener y conservar datos

Desde `CESFAM - V2`, aplica cambios de código, Dockerfile o `.env` con:

```powershell
docker compose up -d --build
```

Operación habitual:

```powershell
docker compose ps
docker compose logs --tail 100 api
docker compose down
```

`down` conserva los volúmenes nombrados. No agregues `-v` si necesitas conservar historiales. `mongo_data` guarda conversaciones de WhatsApp; `chat_history` guarda archivos de la web.

El Pipeline usa documentos y caché copiados a la imagen, sin volumen persistente en el Compose actual. El agente indexa automáticamente si su almacén está vacío. Si modificas documentos con una caché existente, ejecuta explícitamente la indexación:

```powershell
docker compose exec api python -c "from app.application.services.rag_service import RAGAgent; RAGAgent().index_documents()"
```

Este comando modifica la caché del contenedor, no la del anfitrión. Para conservarla entre recreaciones, configura un volumen dedicado para `cache` o exporta el resultado al anfitrión antes de construir otra imagen.

Si cambia la URL de ngrok, actualiza Meta. Al apagar el PC o detener ngrok, Meta deja de poder entregar mensajes al servicio local.

## 13. Servidor permanente

Para disponibilidad continua:

1. Copia el repositorio completo y configura `.env` en el servidor.
2. Inicia Docker y comprueba API, MongoDB y agente.
3. Publica mediante dominio HTTPS estable, proxy inverso o túnel mantenido en ese servidor.
4. Configura en Meta esa URL terminada en `/webhook` y verifica `messages`.
5. Configura `META_APP_SECRET`, políticas de reinicio, respaldos y seguimiento de errores.
6. Restringe MongoDB y las rutas administrativas de la API.

El Compose actual no incluye proxy HTTPS ni políticas `restart`, y publica MongoDB en el puerto 27017 sin configurar autenticación. Adapta esa configuración antes de exponer un servidor. Publicar el puerto 1218 también expone las demás rutas de la API: revisa sus controles de acceso.

El procesamiento ocurre en segundo plano dentro del proceso, sin cola duradera ni deduplicación por identificador de mensaje. Considera estas mejoras para manejar reinicios y reintentos de Meta en producción.

## Referencias

- [Instalación y autenticación de ngrok](https://ngrok.com/download/windows).
- [API de mensajes de Meta y permiso de mensajería](https://www.postman.com/meta/whatsapp-business-platform/folder/13382743-ba8d099d-007e-4b52-b9f2-3cf3c60e4fbc).
- [Suscripciones de webhooks y permiso de administración](https://www.postman.com/meta/whatsapp-business-platform/folder/ypn8q0n/webhook-subscriptions).
- [URL alternativa por WABA](https://www.postman.com/meta/whatsapp-business-platform/request/un84tul/override-callback-url).
- [Documentación de Cloud API mantenida por Meta](https://www.postman.com/meta/whatsapp-business-platform/documentation/wlk6lh4/whatsapp-cloud-api).
