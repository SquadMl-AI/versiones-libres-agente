#!/bin/bash
# Activa el entorno virtual y lanza el servidor FastAPI desde la raíz del backend
cd "$(dirname "$0")"
export ELASTIC_CLIENT_APIVERSIONING=8
source ../../venv/bin/activate
exec uvicorn app.main:app --reload --host 0.0.0.0 --port 5555
