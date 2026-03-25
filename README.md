# Proyecto Memorias 975 – Documentación General

## Descripción
Memorias 975 es una aplicación web para la exploración, búsqueda y síntesis de información sobre justicia y paz, combinando un frontend moderno en React+Vite y un backend robusto en FastAPI. Integra modelos de lenguaje (LLM), Elasticsearch y visualización de grafos.

---

## Estructura del Proyecto

- `backend/` – API y lógica de negocio (FastAPI, Python)
- `frontend/` – Interfaz de usuario (React, Vite)
- `requirements.txt` – Dependencias Python 
- `package.json` (en frontend) – Dependencias Node.js

---

## Requisitos

### Backend
- Python 3.10+
- Elasticsearch en ejecución
- (Opcional) Entorno virtual Python

### Frontend
- Node.js 18+
- npm

---

## Instalación

### Backend
1. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
2. (Opcional) Activa tu entorno virtual:
   ```bash
   source venv/bin/activate
   ```
3. Instala soporte para WebSockets y ejecución recomendada de FastAPI:
   ```bash
   pip install 'uvicorn[standard]'
   ```
4. Configura las variables de entorno necesarias (ver `.env.example` si existe).

### Frontend
1. Instala las dependencias:
   ```bash
   cd frontend
   npm install
   ```

---

## Ejecución

### 1. Iniciar el backend (FastAPI)

Activa el entorno virtual y ejecuta el backend en el puerto 5555:

```bash
cd /home/canequero/APP975
source venv/bin/activate
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 5555 --reload
```

Esto levanta FastAPI en http://localhost:5555

### 2. Iniciar el frontend (Vite)

En otra terminal, ejecuta:

```bash
cd /home/canequero/APP975/frontend
npm run dev -- --port 5556
```

Esto levanta la app en http://localhost:5556

---

## Arquitectura y Componentes

- **Backend (FastAPI):** API REST, endpoints en `app/api/v1/endpoints/`, lógica en `app/services/`, modelos Pydantic en `app/schemas/`.
- **Frontend (React+Vite):** Componentes en `src/components/`, comunicación con backend vía `fetch`.
- **Elasticsearch:** Motor de búsqueda documental.
- **Modelos LLM:** Integración con OpenAI, Azure, Gemini, Bedrock, Phi 4.
- **Visualización de grafos:** Usando Vis.js y @neo4j-nvl/react.

---

## Notas
- Si cambias la URL del backend, actualízala en `frontend/src/api.js`.
- Para producción, usa `npm run build` en frontend y sirve la carpeta `dist/`.
- Ajusta las variables de entorno y configuración según tu despliegue.

---

## Créditos y contacto
Para dudas o contribuciones, consulta la documentación interna o contacta al equipo de desarrollo.
