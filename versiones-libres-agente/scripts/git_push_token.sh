#!/bin/bash
# Script para hacer push a GitHub usando el token del .env
# Uso: bash scripts/git_push_token.sh "Mensaje de commit"

set -e

# Cargar variables del .env
ENV_PATH="$(dirname "$0")/../backend/.env"
if [ -f "$ENV_PATH" ]; then
  export $(grep -v '^#' "$ENV_PATH" | xargs)
else
  echo "No se encontró el archivo .env en $ENV_PATH"
  exit 1
fi

if [ -z "$GITHUB_TOKEN" ]; then
  echo "No se encontró GITHUB_TOKEN en el .env"
  exit 1
fi

if [ -z "$GITHUB_REPO" ]; then
  echo "No se encontró GITHUB_REPO en el .env"
  exit 1
fi

COMMIT_MSG=${1:-"Actualización automática"}

git add .
git commit -m "$COMMIT_MSG" || echo "Nada para commitear"

# Configura el remote temporalmente con el token
GIT_URL="https://${GITHUB_TOKEN}@${GITHUB_REPO#https://}"
git push "$GIT_URL" HEAD:main

echo "Push realizado con token. Recuerda NO subir el .env al repo público."
