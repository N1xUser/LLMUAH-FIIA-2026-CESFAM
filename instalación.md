# Instalación del chatbot CESFAM en WhatsApp

Esta guía permite instalar desde cero el proyecto en Windows y probarlo con WhatsApp. Ejecuta Docker y ngrok en el mismo computador. Para arquitectura, audio, configuración avanzada y despliegue permanente, consulta el [README](README.md).

Los comandos se ejecutan en PowerShell. Sustituye los valores entre `<...>` por los de tu cuenta. No necesitas instalar Python ni MongoDB en Windows: Docker los proporciona.

## 1. Preparar el computador

1. Instala [Docker Desktop para Windows](https://docs.docker.com/desktop/setup/install/windows-install/) siguiendo sus requisitos de sistema y configuración de WSL 2.
2. Reinicia el equipo si el instalador lo solicita.
3. Abre Docker Desktop y espera a que el motor esté iniciado. Utiliza contenedores Linux para este proyecto.
4. Abre PowerShell y comprueba:

```powershell
docker version
docker compose version
```

El primer comando debe mostrar tanto el cliente como el servidor. Si no muestra el servidor, comprueba que Docker Desktop esté abierto.

## 2. Obtener el proyecto

Copia o descarga el repositorio completo a una carpeta de trabajo. Debe conservar esta estructura:

```text
LLMUAH-FIIA-2026-CESFAM/
  README.md
  instalación.md
  CESFAM - V2/
    .env.example
    Dockerfile
    docker-compose.yml
    app/
  CESFAM - Pipeline/
    Model/Agent/Cloud/
      agent.py
      llm_service.py
      Process/
```

Abre PowerShell en la carpeta principal o entra con:

```powershell
Set-Location 'C:\ruta\LLMUAH-FIIA-2026-CESFAM'
```

No copies solamente `CESFAM - V2`: la imagen también necesita el Pipeline y sus documentos de conocimiento.

## 3. Preparar las cuentas y credenciales

### Gemini

Obtén una API key siguiendo la [documentación de Google](https://ai.google.dev/gemini-api/docs/api-key). Verifica que tu cuenta tenga acceso a los modelos definidos en `CESFAM - Pipeline/Model/Agent/Cloud/llm_service.py`.

El RAG actual toma sus nombres de modelos de ese archivo. Cambiar únicamente `GEMINI_MODEL` en `.env` no cambia el modelo de generación del Pipeline.

### Meta WhatsApp Cloud API

En Meta Developers, prepara una aplicación con WhatsApp y una cuenta de WhatsApp Business (WABA). Habilita un número para Cloud API y obtiene:

- Access token con acceso al número y a la WABA.
- Identificador de número de teléfono.
- Identificador de la cuenta WhatsApp Business.
- Secreto de la aplicación Meta.
- Versión de Graph API vigente para tu aplicación.

El envío requiere `whatsapp_business_messaging`; la administración de suscripciones requiere `whatsapp_business_management`. Consulta la [documentación de Meta](https://www.postman.com/meta/whatsapp-business-platform/documentation/wlk6lh4/whatsapp-cloud-api) para permisos y restricciones de tu cuenta. Si usas el número de prueba de Meta, configura los destinatarios permitidos.

Anota el teléfono visible asociado al identificador. Ese es el número al que enviarás mensajes; el identificador no es el teléfono con prefijo internacional.

## 4. Crear la configuración local

Desde la carpeta principal, crea `.env` solo si todavía no existe:

```powershell
if (-not (Test-Path -LiteralPath 'CESFAM - V2/.env')) {
    Copy-Item 'CESFAM - V2/.env.example' 'CESFAM - V2/.env'
}
notepad 'CESFAM - V2/.env'
```

Completa o agrega estas variables, guarda y cierra el editor:

```dotenv
GEMINI_API_KEY=<API_KEY_GEMINI>
META_ACCESS_TOKEN=<ACCESS_TOKEN_META>
META_PHONE_NUMBER_ID=<ID_NUMERO_BOT>
META_WHATSAPP_BUSINESS_ACCOUNT_ID=<ID_WABA>
META_VERIFY_TOKEN=<TOKEN_VERIFICACION_ELEGIDO_POR_TI>
META_APP_SECRET=<SECRETO_APLICACION_META>
META_API_VERSION=<VERSION_GRAPH_API>
MONGO_DB_NAME=generative_rag
```

Elige un token de verificación y utiliza exactamente el mismo en Meta. No es el access token de Meta ni el authtoken de ngrok. `META_APP_SECRET` permite comprobar las firmas de los mensajes entrantes; el código lo reconoce aunque no esté en el archivo de ejemplo.

El Compose del repositorio configura automáticamente `mongodb://mongo:27017` para conectar al MongoDB incluido. No necesitas una cuenta de Atlas para esta instalación. Los valores de MongoDB definidos en `environment` de Compose tienen prioridad sobre `.env`.

Mantén las credenciales fuera de archivos compartidos. El Dockerfile copia las carpetas del proyecto, por lo que debes excluir `.env` mediante `.dockerignore` antes de distribuir la imagen a terceros.

## 5. Construir e iniciar el chatbot

```powershell
Set-Location 'CESFAM - V2'
docker compose up -d --build
docker compose ps
```

La primera construcción descarga dependencias y puede tardar. Deben aparecer los servicios `api` y `mongo` en ejecución.

Comprueba el backend:

```powershell
(Invoke-WebRequest 'http://localhost:1218/' -UseBasicParsing).StatusCode
```

Resultado esperado: `200`. Abre `http://localhost:1218/`, completa el captcha de la web y prueba un saludo y una consulta de salud intercultural. La primera consulta puede necesitar crear embeddings si no existe una caché.

Para ver errores:

```powershell
docker compose logs --tail 100 api
```

El historial de WhatsApp depende de MongoDB; una web que responde no prueba por sí sola el flujo de WhatsApp.

## 6. Instalar y autenticar ngrok

Abre otra terminal e instala siguiendo la [guía oficial de ngrok](https://ngrok.com/download/windows):

```powershell
winget install ngrok -s msstore
```

Si acabas de instalarlo, abre PowerShell nuevamente y comprueba:

```powershell
ngrok version
```

Inicia sesión en tu cuenta de ngrok, obtiene el authtoken del panel y configúralo localmente:

```powershell
ngrok config add-authtoken '<AUTHTOKEN_NGROK>'
ngrok config check
```

Si utilizas la instalación independiente preparada en este equipo, sustituye `ngrok` por:

```powershell
& "$env:LOCALAPPDATA\CESFAM-tools\ngrok\ngrok.exe" version
```

La misma ruta sirve para los subcomandos `config` y `http`.

## 7. Abrir el túnel

En el PC donde corre Docker:

```powershell
ngrok http 1218
```

Si tu cuenta tiene un dominio asignado:

```powershell
ngrok http 1218 --url https://<TU_DOMINIO>.ngrok-free.dev
```

Mantén esa terminal abierta. La salida debe indicar que la URL HTTPS reenvía a `http://localhost:1218`.

No utilices el puerto 80 para este Compose. Si ngrok corre en el PC de un colega, su `localhost` no corresponde a tu equipo; consulta el README para la variante entre dos computadores.

Desde otra terminal, comprueba la URL mostrada por ngrok:

```powershell
(Invoke-WebRequest 'https://<TU_DOMINIO>.ngrok-free.dev/openapi.json' `
    -Headers @{'ngrok-skip-browser-warning'='1'} -UseBasicParsing).StatusCode
```

Resultado esperado: `200`. Conserva la URL pública para el siguiente paso.

## 8. Conectar Meta al chatbot

En la configuración de WhatsApp o Webhooks de tu aplicación Meta:

1. Selecciona la configuración correspondiente a `whatsapp_business_account`.
2. Introduce la URL pública completa:

   ```text
   https://<TU_DOMINIO>.ngrok-free.dev/webhook
   ```

3. Introduce el valor exacto de `META_VERIFY_TOKEN`.
4. Verifica y guarda.
5. Suscribe el campo `messages`.
6. Comprueba que la aplicación está suscrita a la WABA que contiene el número del bot.

Las secciones del panel pueden variar. La verificación debe producir un GET con respuesta `200` en los logs de Docker. La suscripción a `messages` permite recibir los POST de mensajes.

Si hay una URL alternativa configurada por WABA, actualízala también: puede tener prioridad sobre la URL general de la aplicación. El README describe la consulta y modificación de `override_callback_uri` mediante Graph API.

## 9. Probar la instalación completa

En una terminal situada en `CESFAM - V2`:

```powershell
docker compose logs -f api
```

Desde otro WhatsApp:

1. Escribe al teléfono asociado al `META_PHONE_NUMBER_ID` configurado.
2. Envía `Hola`.
3. Envía `¿Qué es un facilitador intercultural?`.
4. Comprueba que aparecen POST del webhook en Docker y que llegan respuestas apropiadas para ambas consultas.

La instalación queda comprobada cuando un mensaje real llega a este contenedor y vuelve una respuesta a WhatsApp. Un GET exitoso solo comprueba la verificación; un POST `200` confirma recepción, pero aún puede haber errores posteriores del agente o del envío.

La configuración base cubre texto. Para notas de voz, instala además `ffmpeg` dentro de la imagen y configura los modelos de transcripción y síntesis según la sección de audio del README.

## 10. Encender, actualizar y detener

Para volver a iniciar en otra sesión, abre Docker Desktop y ejecuta desde `CESFAM - V2`:

```powershell
docker compose up -d
```

Después inicia ngrok de nuevo. Si cambia la URL pública, actualiza Meta.

Para aplicar cambios de código o configuración:

```powershell
docker compose up -d --build
```

Para detener, presiona `Ctrl+C` en la terminal de ngrok y ejecuta:

```powershell
docker compose down
```

No agregues `-v` si deseas conservar los historiales de los volúmenes. El computador, Docker y el túnel deben permanecer activos para recibir mensajes.

## 11. Si algún paso falla

| Problema | Acción |
| --- | --- |
| Docker no conecta con el motor | Abre Docker Desktop y espera su inicio |
| Puertos ocupados | Revisa qué servicio utiliza 1218, 1219 o 27017 antes de iniciar Compose |
| ngrok no se reconoce | Abre otra terminal o utiliza la ruta completa de su ejecutable |
| `ERR_NGROK_4018` | Configura un authtoken válido de ngrok |
| URL pública devuelve `404` | Comprueba que el túnel apunta a 1218 y al PC de Docker |
| Meta no verifica | Revisa URL completa, túnel activo y token idéntico |
| Solo hay GET, ningún mensaje | Revisa número, WABA, suscripción `messages` y URL alternativa |
| Responde otro bot | Confirma que el número del chat corresponde al identificador configurado |
| Hay POST pero no respuesta | Consulta logs posteriores: MongoDB, Gemini, permisos y access token |
| Falla Gemini | Comprueba clave, cuotas y modelos definidos en el Pipeline |

Para diagnóstico detallado, persistencia de la caché y requisitos de producción, consulta el [README](README.md).
