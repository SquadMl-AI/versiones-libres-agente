# Documentación de Archivos del Proyecto Memorias 975

Este documento describe brevemente la función de cada archivo y carpeta principal en las carpetas `frontend` y `backend`.

## Frontend (`frontend/`)

- **README.md**: Instrucciones de instalación y uso del frontend.
- **package.json**: Dependencias y scripts del proyecto React.
- **vite.config.js**: Configuración de Vite para el build y desarrollo.
- **eslint.config.js**: Configuración de ESLint para el linting del código.
- **index.html**: HTML principal de la app React.
- **src/**: Código fuente principal de React.
  - **App.jsx**: Componente raíz de la aplicación React.
  - **main.jsx**: Punto de entrada de la app, renderiza el componente principal.
  - **api.js**: Funciones para interactuar con el backend vía HTTP/WebSocket.
  - **App.css, index.css**: Estilos globales de la app.
  - **assets/**: Recursos estáticos (imágenes, SVGs).
  - **components/**: Componentes React reutilizables (tabs, formularios, visualizaciones, etc.).
    - **AboutTab.jsx**: Pestaña de información general.
    - **ChatTab.jsx**: Pestaña de chat.
    - **DashboardTab.jsx**: Pestaña de dashboard de resultados.
    - **EmailPrompt.jsx**: Componente para solicitar email al usuario.
    - **GraphViewer.jsx**: Visualización de grafos de resultados.
    - **MultiSelect.jsx**: Selector múltiple reutilizable.
    - **SherlockTab.jsx**: Pestaña de búsqueda avanzada.
    - **SimpleSearchTab.jsx**: Pestaña de búsqueda simple y principal.
    - **StarRating.jsx**: Componente de calificación por estrellas.
    - **TermsOfUse.jsx**: Términos de uso.
    - **VisNetworkGraph.jsx**: Visualización de grafos con vis-network.
  - **schemas/**: Archivos JSON con catálogos de colecciones y documentos.

## Backend (`backend/`)

- **README_BACKEND.md**: Instrucciones y detalles del backend.
- **DB_SCHEMA.md**: Esquema y descripción de la base de datos.
- **start_all.sh, start_api.sh**: Scripts para iniciar los servicios del backend.
- **health_check.sh**: Script para verificar el estado del backend.
- **app/**: Código fuente principal del backend (FastAPI + lógica de negocio).
  - **main.py**: Punto de entrada de la API FastAPI.
  - **busqueda_escloud.py**: Lógica de búsqueda híbrida en Elasticsearch.
  - **model_handlers.py**: Manejo de modelos LLM y embeddings.
  - **test_es_connection.py**: Script para probar la conexión a Elasticsearch.
  - **utils_helpers.py**: Funciones utilitarias generales.
  - **api/**: Endpoints de la API REST y WebSocket.
    - **v1/endpoints/**: Endpoints organizados por funcionalidad (búsqueda, feedback, síntesis, etc.).
  - **db/**: Conexión y utilidades para Elasticsearch.
  - **logs/**: Archivos de logs del backend.
  - **prompts/**: Prompts usados para síntesis y resumen con LLM.
  - **schemas/**: Esquemas de datos y validaciones.
  - **services/**: Lógica de negocio y servicios (búsqueda, chat, dashboard, etc.).
  - **utils/**: Scripts utilitarios para auditoría, extracción y actualización de catálogos.

- **schemas/**: Catálogos y mapeos de colecciones/documentos.
- **scripts/**: Scripts auxiliares para tareas administrativas.

---

> Para detalles adicionales, consulta los archivos README de cada carpeta o el código fuente correspondiente.
