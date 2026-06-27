from app import app
from waitress import serve
import logging

# Configurar logs básicos de producción
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("waitress")

if __name__ == "__main__":
    logger.info("Iniciando servidor de producción WSGI (Waitress) en el puerto 5000...")
    serve(app, host="0.0.0.0", port=5000, threads=4, connection_limit=100)
