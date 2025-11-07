# Dockerfile (producción)
FROM python:3.12-slim

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV TMPDIR=/dev/shm
ENV DJANGO_SETTINGS_MODULE=blog.settings.prod


# Directorio de trabajo
WORKDIR /app

# Copiar requirements (ajustado para Railway)
# Railway usa la raíz del repo como contexto, así que los archivos
# están en blog/requirements/ dentro del contexto.
# -------------------------
COPY blog/requirements/ /app/requirements/

# Instalar dependencias de producción
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements/requirements-prod.txt

# Copiar la app y script de arranque
COPY blog/ /app/

# Dar permisos de ejecución al script de arranque
RUN chmod +x /app/start.sh

# Exponer puerto 8000
EXPOSE 8000

# Usa el script de arranque
CMD ["bash", "/app/start.sh"]
