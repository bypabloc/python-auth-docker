FROM python:3.12

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # pip
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /app

# Instalar dependencias
COPY requirements /app/requirements
RUN pip install -r requirements

# No copiar el código aquí para permitir hot reload
# El código se montará como volumen
