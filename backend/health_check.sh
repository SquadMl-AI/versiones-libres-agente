#!/bin/bash
# Script: health_check.sh
# Uso: ./health_check.sh [host] [port]
# Por defecto: host=localhost, port=5555

HOST=${1:-localhost}
PORT=${2:-5555}

URL="http://$HOST:$PORT/health"

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # Sin color
CHECK='✔'
FAIL='✖'

resp=$(curl -s "$URL")
if [ -z "$resp" ]; then
  echo -e "${RED}No se pudo conectar al backend en $URL${NC}"
  exit 1
fi

# Usar jq para parsear el JSON de la respuesta
if ! command -v jq &> /dev/null; then
  echo "Por favor instala jq: sudo apt install jq"
  exit 1
fi

printf "\nEstado de servicios (checklist):\n"
echo "$resp" | jq -r '.checks[] | "\(.service)|\(.ok)|\(.msg)"' | while IFS='|' read -r service ok msg; do
  if [ "$ok" = "true" ] || [ "$ok" = "True" ]; then
    echo -e "${GREEN}$CHECK $service${NC} - $msg"
  else
    echo -e "${RED}$FAIL $service${NC} - $msg"
  fi
done
