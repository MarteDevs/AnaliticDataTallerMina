# Guía de Despliegue en Producción (VPS con PM2 y Nginx)

Esta guía documenta los pasos necesarios para desplegar la aplicación de Análisis de Datos de Taller Mina en un VPS propio utilizando **PM2** como administrador de procesos y **Nginx** como servidor web (Proxy Reverso) con certificados SSL gratuitos (HTTPS).

---

## Prerrequisitos en el VPS (Basado en Ubuntu / Debian)

1. Actualizar el servidor e instalar dependencias básicas:
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install git python3-pip python3-venv nodejs npm nginx -y
   ```

2. Instalar **PM2** de manera global con npm:
   ```bash
   sudo npm install pm2 -g
   ```

---

## Paso 1: Subir el Proyecto y Configurar el Código

1. Clonar o subir tu proyecto al directorio web del VPS (por ejemplo, `/var/www/AnalisisData`):
   ```bash
   sudo mkdir -p /var/www/AnalisisData
   sudo chown -R $USER:$USER /var/www/AnalisisData
   cd /var/www/AnalisisData
   # Clonar el repositorio o subir archivos aquí
   ```

2. Crear y activar el entorno virtual de Python:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Instalar las dependencias de producción:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

---

## Paso 2: Configuración e Inicio con PM2

1. Abre el archivo `ecosystem.config.js` que se encuentra en la raíz del proyecto y ajusta el campo `cwd` con la ruta absoluta donde colocaste la aplicación en tu VPS:
   ```javascript
   cwd: "/var/www/AnalisisData", // <-- Asegúrate de que coincida con tu ruta en el VPS
   ```

2. Levantar la aplicación con PM2:
   ```bash
   pm2 start ecosystem.config.js
   ```

3. Guardar el estado de PM2 y configurar el auto-arranque en reinicios del VPS:
   ```bash
   pm2 save
   pm2 startup
   ```
   *Nota: El comando `pm2 startup` imprimirá una línea de código que deberás copiar y pegar en tu terminal con privilegios `sudo` para finalizar el registro.*

4. Comandos útiles de PM2:
   * **Ver logs en tiempo real:** `pm2 logs`
   * **Ver estado de la app:** `pm2 status`
   * **Reiniciar la app:** `pm2 restart analisis-data-taller`
   * **Detener la app:** `pm2 stop analisis-data-taller`

---

## Paso 3: Configurar Nginx (Proxy Reverso)

Para que los usuarios puedan acceder ingresando tu dominio o IP pública en el puerto estándar 80/443, configuraremos Nginx.

1. Crear un archivo de configuración para la app en Nginx:
   ```bash
   sudo nano /etc/nginx/sites-available/analisis-data
   ```

2. Pegar la siguiente configuración (reemplaza `tu-dominio.com` por tu dominio real o IP pública):
   ```nginx
   server {
       listen 80;
       server_name tu-dominio.com; # o IP pública si no tienes dominio

       # Aumentar límite de subida de archivos para Excels grandes (ej. 50MB)
       client_max_body_size 50M;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           
           # Timeouts extendidos para la generación de reportes consolidado pesados
           proxy_read_timeout 150s;
           proxy_connect_timeout 150s;
           proxy_send_timeout 150s;
       }
   }
   ```

3. Habilitar la configuración y reiniciar Nginx:
   ```bash
   sudo ln -s /etc/nginx/sites-available/analisis-data /etc/nginx/sites-enabled/
   sudo nginx -t # Validar que no haya errores de sintaxis
   sudo systemctl restart nginx
   ```

---

## Paso 4: Seguridad SSL con HTTPS (Certbot)

Si tienes un dominio apuntando al VPS, es altamente recomendable instalar HTTPS de forma gratuita con Let's Encrypt:

1. Instalar Certbot para Nginx:
   ```bash
   sudo apt install certbot python3-certbot-nginx -y
   ```

2. Obtener e instalar el certificado SSL (Certbot modificará automáticamente Nginx y configurará la renovación automática):
   ```bash
   sudo certbot --nginx -d tu-dominio.com
   ```

¡Felicidades! Tu aplicación ya estará desplegada de manera segura, con auto-reinicio, y accesible para todos a través de HTTPS.
