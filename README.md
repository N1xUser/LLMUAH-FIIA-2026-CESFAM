<div style="font-family: apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-weight: bold;">

# CESFAM Chatbot

Este proyecto es un servicio completo compuesto por una aplicacion web backend/frontend y un pipeline de vectorizacion y RAG basado en IA generativa.

## Componentes

El proyecto ha sido restructurado en dos partes principales:

* **CESFAM - V2**: Aplicacion backend/frontend basada en FastAPI. Actua como la interfaz principal e incluye la API para el chat y manejo de historial.
* **CESFAM - Pipeline**: Contiene la logica subyacente para el agente RAG (Retrieval-Augmented Generation) y la vectorizacion de datos en base a documentos locales.

## Caracteristicas principales

* **Interfaz de Chat Minimalista**: Una interfaz web para que los usuarios interactuen con el asistente, con soporte de scroll para historiales extensos.
* **Sesiones de 30 minutos**: Cuenta con un sistema de captcha que proporciona a los usuarios un token valido por 30 minutos, previniendo abusos por parte de bots.
* **API Key Segura**: La API de consulta de chat utiliza validacion basada en API key almacenada en memoria o validada segun configuracion, previniendo abusos.
* **Almacenamiento Local y Base de Datos**: Guarda el historial de los chats localmente. Ademas, puede interactuar con MongoDB de solo lectura segun necesidades de despliegue y docker-compose.
* **Modelo RAG**: Utiliza un agente interno (Pipeline) para procesar consultas usando embeddings y modelos de lenguaje.
* **Diseno Responsivo**: La interfaz esta adaptada para funcionar correctamente en cualquier dispositivo.

## Estructura del Proyecto

* `CESFAM - V2/`: Aplicacion web y API (FastAPI).
* `CESFAM - Pipeline/`: Agente RAG, scripts de IA y bases de datos vectorizadas.

## Despliegue con Docker

El proyecto utiliza Docker y Docker Compose para facilitar su despliegue y orquestacion, uniendo `CESFAM - V2` y el pipeline del agente RAG.

1. Asegurate de tener Docker y Docker Compose instalados.
2. Configura los archivos `.env` necesarios.
3. Para iniciar la aplicacion, ejecuta:

```bash
cd "CESFAM - V2"
docker compose up -d --build
```

4. El servicio web y la API estaran disponibles a traves de los puertos definidos en `docker-compose.yml` (por defecto, puertos 1218 y 1219 mapeados al puerto 8000 interno del contenedor).

</div>
