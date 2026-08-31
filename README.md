# CESFAM Chatbot

Este proyecto es una aplicacion web sencilla basada en Flask que sirve como interfaz para un chatbot asistente. 

## Caracteristicas principales

* **Interfaz de Chat Minimalista**: Una interfaz web para que los usuarios interactuen con el asistente.
* **Sesiones de 30 minutos**: Cuenta con un sistema de captcha que proporciona a los usuarios un token valido por 30 minutos, previniendo abusos por parte de bots sin necesidad de una base de datos.
* **Almacenamiento Local de Historial**: Guarda el historial de los chats en formato JSON localmente, eliminando la dependencia de una base de datos externa.
* **Modelo RAG (Retrieval-Augmented Generation)**: Utiliza un agente interno para procesar consultas usando embeddings y modelos de lenguaje, consultando documentos locales en formato Markdown.
* **Diseno Responsivo**: La interfaz esta adaptada para funcionar correctamente tanto en computadoras de escritorio como en dispositivos moviles.

## Requisitos

El proyecto esta construido en Python y requiere las siguientes librerias (ver `requirements.txt`):

* Flask
* gunicorn
* python-dotenv
* numpy

## Instalacion y Despliegue en Ubuntu con Nginx, DuckDNS y Let's Encrypt

1. Clona o copia el repositorio en tu servidor.

2. Crea un entorno virtual e instala las dependencias:
   
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Ejecuta el servidor Flask en segundo plano (puedes usar un servicio de systemd, screen o tmux):
   
   ```bash
   cd CESFAM/Host
   python3 app.py
   ```

4. Configura tu dominio en DuckDNS apuntando a la IP publica de tu servidor.

5. Instala Nginx y Certbot:
   
   ```bash
   sudo apt update
   sudo apt install nginx certbot python3-certbot-nginx
   ```

6. Crea un archivo de configuracion en Nginx (por ejemplo, `/etc/nginx/sites-available/cesfam`) como proxy inverso hacia el puerto 5000:
   
   ```nginx
   server {
       listen 80;
       server_name tu-dominio.duckdns.org;
   
       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       }
   }
   ```

7. Habilita el sitio y reinicia Nginx:
   
   ```bash
   sudo ln -s /etc/nginx/sites-available/cesfam /etc/nginx/sites-enabled/
   sudo systemctl restart nginx
   ```

8. Genera tu certificado SSL gratuito con Let's Encrypt:
   
   ```bash
   sudo certbot --nginx -d tu-dominio.duckdns.org
   ```

## Estructura del Proyecto

* `CESFAM/Host/`: Contiene la aplicacion web principal (`app.py`), los archivos estaticos (`static/`) y las plantillas HTML (`templates/`).
* `CESFAM/Model/`: Contiene la logica del agente RAG (`agent.py`) y el motor de procesamiento de documentos.
* `CESFAM/Data/`: Destinada para datos auxiliares.

## Notas Adicionales

* Cada vez que un usuario ingresa a la pagina, se muestra un chat nuevo y en blanco por defecto.
* La verificacion del captcha es en memoria, lo que significa que reiniciar el servidor invalidara los tokens actuales. Esto mantiene la simplicidad del proyecto al no requerir bases de datos.
