#!/bin/bash
# Script para iniciar backend FastAPI y frontend Vite en paralelo

# Iniciar backend (FastAPI)
echo "Iniciando backend FastAPI en puerto 5555..."
cd "$(dirname "$0")"
uvicorn app.main:app --reload --host 0.0.0.0 --port 5555 &
BACKEND_PID=$!

# Iniciar frontend (Vite)
echo "Iniciando frontend Vite en puerto 5556..."
cd ../frontend
npm run dev -- --port 5556 &
FRONTEND_PID=$!

# Esperar a que ambos procesos terminen
wait $BACKEND_PID $FRONTEND_PID
