# 📚 DOCUMENTACIÓN DEL PROYECTO MEMORIAS 975 - BACKEND

---

## 📖 ¿QUÉ ES ESTE PROYECTO?

**Memorias 975** es un **backend de API REST basado en FastAPI** que implementa un sistema **RAG (Retrieval-Augmented Generation)** para búsqueda inteligente,síntesis de información y análisis de documentos.

### 🎯 **Propósito Principal**

Este proyecto proporciona un servicio de **búsqueda avanzada y generación de respuestas** utilizando:
- **Inteligencia Artificial (LLM)** para procesar y sintetizar información
- **Búsqueda semántica** mediante vectores de embeddings
- **Recopilación de feedback** de usuarios para mejorar el sistema
- **Análisis de relevancia** de documentos y colecciones
- **Análisis de grafos** para relaciones entre documentos

El sistema está diseñado para consultores, investigadores y usuarios que necesitan buscar, sintetizar y analizar información compleja de documentos (audiencias, sentencias,reportes, etc.).

### 💡 **Casos de Uso**

1. **Búsqueda semántica**: Encontrar documentos relevantes basados en preguntas en lenguaje natural
2. **Síntesis de información**: Generar respuestas resumidas y contextualizadas
3. **Análisis de grafos**: Visualizar relaciones entre documentos
4. **Feedback y análisis**: Capturar calificaciones de usuarios para mejorar calidad
5. **Reportes y métricas**: Dashboard con estadísticas de uso y rendimiento

---

## 🏗️ **ARQUITECTURA Y ESTRUCTURA DEL PROYECTO**

```
backend/
├── app/                          # 📁 Código principal de la aplicación
│   ├── __init__.py
│   ├── main.py                   # ⚙️ Punto de entrada de la aplicación FastAPI
│   ├── api/                      # 🔌 Rutas y endpoints de la API
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py            # 🎯 Router principal que agrega todos los endpoints
│   │       └── endpoints/        # 📍 Cada archivo define un grupo de endpoints
│   │           ├── advance_search.py         # Búsqueda avanzada
│   │           ├── blobs.py                  # Gestión de archivos y carpetas
│   │           ├── chat_ask.py               # Chat conversacional
│   │           ├── chat.py                   # Chat (legacy/alternativo)
│   │           ├── dashboard.py              # Métricas y estadísticas
│   │           ├── datasets.py               # Gestión de datasets
│   │           ├── feed_messages.py          # Feedback de mensajes
│   │           ├── feedback_synthesis.py     # Feedback de síntesis
│   │           ├── feedback.py               # Feedback general
│   │           ├── grafo.py                  # Análisis de grafos (legacy)
│   │           ├── graph.py                  # Análisis de grafos
│   │           ├── history_session.py        # Historial de sesiones
│   │           ├── search.py                 # Búsqueda básica
│   │           ├── synthesis.py              # Síntesis de chunks
│   │           ├── synthesize.py             # Síntesis (versión alternativa)
│   │           ├── users_auth.py             # Autenticación de usuarios
│   │           ├── graph_service.py          # Servicio de grafos
│   │
│   ├── db/                       # 🗄️ Configuración de bases de datos
│   │   ├── __init__.py
│   │   └── elastic.py            # Cliente y configuración de Elasticsearch
│   │
│   ├── services/                 # 🔧 Lógica de negocio y servicios principales
│   │   ├── __init__.py
│   │   ├── chat_service.py       # Servicio para chat conversacional
│   │   ├── dashboard_service.py  # Servicio para métricas y estadísticas
│   │   ├── graph_service.py      # Servicio para análisis de grafos
│   │   ├── graph.py              # Utilidades para grafos
│   │   ├── indexing_service.py   # Indexación de documentos
│   │   ├── logging_service.py    # Servicio de logging
│   │   ├── rag_service_audiencias.py    # 🎯 Pipeline RAG para audiencias
│   │   ├── rag_service_sentencias.py    # 🎯 Pipeline RAG para sentencias
│   │   ├── relevance_service.py  # Servicio de análisis de relevancia
│   │   ├── search_category_service.py   # Categorización de búsquedas
│   │   ├── search_service.py     # Servicio de búsqueda
│   │   ├── synthesis_service.py  # Servicio de síntesis de información
│   │   └── tools_graph.py        # Herramientas para grafos
│   │
│   ├── prompts/                  # 💬 Templates de prompts para LLM
│   │   ├── __init__.py
│   │   ├── final_synthesis_prompts.py     # Prompts para síntesis final
│   │   ├── simple_synthesis_prompts.py    # Prompts simples
│   │   └── summarize_chunk_prompts.py     # Prompts para resumir chunks
│   │
│   ├── schemas/                  # 📋 Esquemas Pydantic y catálogos
│   │   ├── __init__.py
│   │   └── search.py             # Esquemas para búsqueda
│   │
│   ├── utils/                    # 🛠️ Utilidades y funciones auxiliares
│   │   ├── __init__.py
│   │   ├── ai_services.py        # Integración con servicios Azure/OpenAI
│   │   ├── audit_missing_kb_id.py        # Auditoría de KB IDs faltantes
│   │   ├── extract_fields.py     # Extracción de campos de documentos
│   │   ├── index_config.py       # Configuración de índices Elasticsearch
│   │   ├── indexing_pipeline.py  # Pipeline de indexación
│   │   ├── kb_catalog.py         # Catálogo de knowledge bases
│   │   ├── messages_serialize.py # Serialización de mensajes
│   │   ├── update_document_catalog.py    # Actualización de catálogos
│   │   ├── update_kb_catalog.py  # Actualización de KB
│   │   └── users/                # Utilidades para usuarios
│   │
│   ├── busqueda_escloud.py       # Módulo de búsqueda Elasticsearch Cloud
│   ├── general_tests.ipynb       # Notebook con tests generales
│   ├── indexing.ipynb            # Notebook de indexación
│   ├── indexing.py               # Script de indexación
│   ├── kb_id_to_documents.json   # Catálogo KB → Documentos
│   ├── kb_id_to_name.json        # Catálogo KB → Nombres
│   ├── model_handlers.py         # Manejadores de modelos AI
│   ├── pdfs_data.json            # Información de PDFs
│   ├── test_es_connection.py     # Test de conexión Elasticsearch
│   └── utils_helpers.py          # Funciones auxiliares generales
│
├── schemas/                      # 📂 Esquemas adicionales (nivel raíz)
│   └── extract_tree_kb_id_pdf_and_docid.py  # Extracción de estructura KB
│
├── 📝 Archivos de Configuración y Documentación:
├── requirements.txt              # 📦 Dependencias Python
├── README_BACKEND.md             # 📖 README principal
├── DB_SCHEMA.md                  # 🗄️ Esquema de PostgreSQL
├── Dockerfile                    # 🐳 Contenedor Docker
├── docker-compose.yml            # (probablemente existe)
├── .env                          # ⚙️ Variables de entorno
├── start_api.sh                 # 🚀 Script para iniciar API
├── start_all.sh                 # 🚀 Script para iniciar todo
├── health_check.sh              # 🏥 Health check
├── deploy_acr.sh                # 🚀 Deploy a Azure Container Registry
├── create_interactions.sql       # 🗄️ Script para crear tabla PostgreSQL
└── final_categorized_chunks.json # Chunks categorizados

```

---

## 🔌 **COMPONENTES PRINCIPALES**

### 1. **FastAPI Backend (`app/main.py`)**
- **Framework**: FastAPI (Python)
- **Función**: Servidor HTTP que expone los endpoints de la API
- **Características**:
  - CORS habilitado para comunicación con frontend
  - Health checks para verificar servicios dependientes
  - Routing modular por feature

### 2. **API REST (`app/api/v1/`)**
**Endpoints activos registrados en `api.py`:**

| Prefix | Módulo | Descripción |
|--------|--------|-------------|
| `/chat_ask` | `chat_ask.py` | Chat conversacional con RAG |
| `/synthesis_chuks` | `synthesis.py` | Síntesis de chunks individuales |
| `/advance_search` | `advance_search.py` | Búsqueda avanzada |
| `/sessions` | `history_session.py` | Gestión de historial de sesiones |
| `/folders` | `blobs.py` | Gestión de carpetas |
| `/files` | `blobs.py` | Gestión de archivos |
| `/users_auth` | `users_auth.py` | Autenticación y gestión de usuarios |
| `/` (feedback) | `feedback_synthesis.py` | Endpoints de feedback |

### 3. **Servicios Core (`app/services/`)**

#### **RAG Services** 🎯
- **`rag_service_audiencias.py`**: Pipeline RAG especializado para documentos de audiencias
  - Busca documentos relevantes
  - Genera respuestas con citas
  - Estructura: `RAGPipelineAudiencias` class
  
- **`rag_service_sentencias.py`**: Pipeline RAG para sentencias judiciales

#### **Búsqueda y Relevancia**
- **`search_service.py`**: Búsqueda semántica en Elasticsearch
- **`relevance_service.py`**: Análisis de relevancia de documentos
- **`search_category_service.py`**: Categorización de búsquedas

#### **Síntesis y Generación**
- **`synthesis_service.py`**: Síntesis de información de chunks
- **`chat_service.py`**: Conversaciones con historial

#### **Análisis y Reportes**
- **`dashboard_service.py`**: Métricas de uso y estadísticas
- **`graph_service.py`**: Análisis de relaciones entre documentos
- **`logging_service.py`**: Registro detallado de operaciones

### 4. **Bases de Datos**

#### **Elasticsearch** 🔍
- **Función**: Búsqueda de texto completo y búsqueda semántica
- **Índices**: Documentos categorizados (audiencias, sentencias, etc.)
- **Características**:
  - Búsqueda vectorial (embeddings)
  - Búsqueda de texto convencional
  - Filtrado por metadata
- **Configuración**: `app/db/elastic.py` y `app/utils/index_config.py`

#### **PostgreSQL** 🗄️
- **Función**: Almacenar feedback y analytics de usuarios
- **Base**: `feedback975`
- **Tabla principal**: `interactions`
  - Captura: consultas, síntesis, feedback, ratings
  - Analytics: evolución de uso, satisfacción
- **Esquema**: Documentado en `DB_SCHEMA.md`

#### **Azure Cosmos DB** ☁️
- **Función**: Base de datos NoSQL para datos complejos
- **Uso**: Grafos de relaciones, datos de sesiones, configuraciones
- **Variables de entorno**:
  - `AZURE_COSMOSDB_DATABASE_NAME`
  - `AZURE_COSMOSDB_COLLECTION_NAME`
  - `AZURE_COSMOSDB_ENDPOINT`

### 5. **Inteligencia Artificial**

#### **Azure OpenAI** 🤖
- **Modelos**:
  - `gpt-4.1-mini`: Procesamiento de lenguaje y síntesis
  - `gpt-4`: Tareas más complejas
  - `text-embedding-3-large`: Generación de embeddings
- **Endpoints configurados en variables de entorno**:
  - `GPT41MINI_ENDPOINT` / `GPT41MINI_API_KEY`
  - `EMBEDDING_ENDPOINT` / `EMBEDDING_API_KEY`

#### **Azure AI Services** 🔧
- Azure Form Recognizer: Extracción de formularios
- Azure Search Documents: Búsqueda inteligente
- Azure Text Analytics: Análisis de texto

### 6. **Utilidades** (`app/utils/`)
- **`ai_services.py`**: Wrapper unificado para servicios Azure/OpenAI
- **`index_config.py`**: Configuración de índices Elasticsearch
- **`indexing_pipeline.py`**: Flujo de indexación de documentos
- **`kb_catalog.py`**: Gestión del catálogo de Knowledge Bases
- **`messages_serialize.py`**: Serialización de mensajes para persistencia
- **`extract_fields.py`**: Extracción estructurada de campos

### 7. **Prompts** (`app/prompts/`)
Templates paramétricos para:
- Síntesis final de información
- Síntesis simple
- Resumen de chunks
- Generación de respuestas contextualizadas

---

## 📊 **FLUJO DE DATOS PRINCIPAL**

```
┌─────────────────┐
│  Cliente (Web)  │
└────────┬────────┘
         │ HTTP Request
         ▼
┌──────────────────────────────────────┐
│   FastAPI Router (/chat_ask, etc)    │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│      Servicios (Service Layer)       │
│  - RAGPipeline                       │
│  - SearchService                     │
│  - SynthesisService                  │
└────────┬─────────────────────────────┘
         │
    ┌────┴────┬───────────┬──────────┐
    │          │           │          │
    ▼          ▼           ▼          ▼
┌────────┐ ┌─────────┐ ┌──────┐ ┌─────────┐
│   ES   │ │  Azure  │ │Cosmos│ │   PG    │
│Search  │ │ OpenAI  │ │  DB  │ │Feedback │
└────────┘ └─────────┘ └──────┘ └─────────┘

1. Query llega a endpoint
2. Servicio busca documentos relevantes en Elasticsearch
3. Enriquece con embeddings de Azure OpenAI
4. Aplica filtros de relevancia
5. Genera síntesis con gpt-4.1-mini
6. Registra interacción en PostgreSQL
7. Devuelve respuesta con citas al cliente
```

---

## 🚀 **FLUJO DE DESARROLLO Y DEPLOYMENT**

### **Instalación Local**
```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar .env con credentials Azure/OpenAI/Elasticsearch
# Ver variables en .env.example (si existe)

# 3. Iniciar API
python -m uvicorn app.main:app --reload
```

### **Docker**
```bash
# Build
docker build -t rag975-backend .

# Run
docker run -p 8000:8000 --env-file .env rag975-backend
```

### **Scripts Disponibles**
- `start_api.sh`: Inicia solo la API FastAPI
- `start_all.sh`: Inicia API + servicios dependientes
- `deploy_acr.sh`: Deploya a Azure Container Registry
- `health_check.sh`: Verifica salud de servicios

### **Tests**
- `app/general_tests.ipynb`: Tests generales
- `app/indexing.ipynb`: Tests de indexación
- `app/test_es_connection.py`: Verificar conexión Elasticsearch

---

## 🔐 **VARIABLES DE ENTORNO REQUERIDAS**

### **Base de Datos**
```
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=feedback975
POSTGRES_USER=user
POSTGRES_PASSWORD=password

ELASTICSEARCH_HOST=http://localhost:9200
ES_API_KEY=your_es_api_key

AZURE_COSMOSDB_ENDPOINT=https://...
AZURE_COSMOSDB_DATABASE_NAME=db_name
AZURE_COSMOSDB_COLLECTION_NAME=collection_name
```

### **Azure OpenAI**
```
GPT41MINI_ENDPOINT=https://...
GPT41MINI_API_KEY=key

EMBEDDING_ENDPOINT=https://...
EMBEDDING_API_KEY=key
```

### **Azure Services**
```
AZURE_SEARCH_SERVICE_ENDPOINT=...
AZURE_SEARCH_SERVICE_API_KEY=...

AZURE_FORM_RECOGNIZER_ENDPOINT=...
AZURE_FORM_RECOGNIZER_API_KEY=...
```

---

## 📈 **TABLA DE FEEDBACK Y ANALYTICS**

La tabla `interactions` en PostgreSQL captura:

| Campo | Propósito |
|-------|-----------|
| `query` | Pregunta original del usuario |
| `model_name_relevance` | Qué modelo filtró documentos |
| `synthesis` | Respuesta generada |
| `relevance_feedback` | ⭐ Calificación de relevancia |
| `synthesis_feedback` | ⭐ Calificación de síntesis |
| `rating` | Calificación general |
| `timestamp` | Cuándo se realizó |
| `user_email` / `session_id` | Quién lo hizo |

**Métrica clave**: Dashboard expone evolución de satisfacción (últimos 30 días).

---

## 🔍 **ENDPOINTS PRINCIPALES**

```
POST   /api/v1/chat_ask        → Chat conversacional
POST   /api/v1/synthesis_chuks → Síntesis de chunks
POST   /api/v1/advance_search  → Búsqueda avanzada
GET    /api/v1/sessions        → Historial de sesiones
POST   /api/v1/feedback/*      → Registrar feedback
GET    /api/v1/dashboard/*     → Métricas y estadísticas
```

---

## 📚 **DEPENDENCIAS CLAVE** (`requirements.txt`)

| Dependencia | Uso |
|-------------|-----|
| `fastapi`, `uvicorn` | Framework API |
| `elasticsearch` | Cliente de búsqueda |
| `openai`, `azure-*` | Integración Azure OpenAI |
| `azure-cosmos` | Base datos NoSQL |
| `psycopg2-binary` | Driver PostgreSQL |
| `pydantic` | Validación de datos |
| `langchain`, `langgraph` | Orquestación de IA |
| `pymupdf` | Lectura de PDFs |
| `networkx`, `pyvis` | Análisis y visualización de grafos |
| `beautifulsoup4` | Parsing HTML |
| `pandas`, `matplotlib`, `altair` | Análisis y visualización datos |

---

## 🎯 **RESUMEN EJECUTIVO**

| Aspecto | Descripción |
|--------|-------------|
| **Lenguaje** | Python (FastAPI) |
| **Propósito** | RAG Backend para búsqueda + síntesis inteligente |
| **Arquitectura** | Microservicios con orquestación de IA |
| **Bases de datos** | Elasticsearch (búsqueda), PostgreSQL (feedback), Cosmos DB (datos) |
| **IA** | Azure OpenAI (gpt-4.1-mini, embeddings) |
| **Autenticación** | Email/Session ID |
| **Analytics** | Dashboard con métricas en tiempo real |
| **Deployment** | Docker + Azure Container Registry |

---

## 📝 **NOTAS IMPORTANTES**

1. **Configuración crítica**: El proyecto requiere credenciales válidas de Azure OpenAI y Elasticsearch para funcionar
2. **Base datos feedback**: Debe existir base `feedback975` en PostgreSQL antes de ejecutar
3. **Índices**: Los índices de Elasticsearch deben estar correctamente poblados con documentos
4. **Prompts parametrizado**: Los prompts para IA se pueden customizar en `app/prompts/`
5. **Escalabilidad**: Diseñado para manejar múltiples sesiones concurrentes con FastAPI async

---

**Última actualización**: Febrero 2026
**Versión**: 1.0

