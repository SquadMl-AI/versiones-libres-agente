# Proyecto Memorias 975 - Backend

---

## Esquema de la base de datos: Tabla `interactions`

> **Referencia rápida:** El esquema detallado y la descripción de cada campo están en [`DB_SCHEMA.md`](./DB_SCHEMA.md).

### Descripción de los campos de la tabla `interactions`

| Campo                          | Tipo           | Descripción |
|--------------------------------|----------------|-------------|
| id                             | SERIAL         | Identificador único autoincremental de cada registro. |
| timestamp                      | TIMESTAMP      | Fecha y hora en que se registró el feedback. |
| user_email                     | VARCHAR(255)   | Correo electrónico del usuario que envía el feedback. |
| session_id                     | VARCHAR(255)   | Identificador de sesión del usuario (puede ser null). |
| ip_address                     | VARCHAR(64)    | Dirección IP desde donde se envió el feedback. |
| query                          | TEXT           | Consulta original realizada por el usuario. |
| model_name_relevance           | VARCHAR(128)   | Nombre del modelo LLM usado para la búsqueda de relevancia. |
| model_name_synthesis           | VARCHAR(128)   | Nombre del modelo LLM usado para la síntesis. |
| relevance_filtered_collections  | TEXT           | Colecciones filtradas por relevancia (puede ser texto plano o JSON serializado). |
| relevance_filtered_collections_flag | INT        | Indicador/flag asociado al filtrado de colecciones. |
| relevance_filtered_documents    | TEXT           | Documentos filtrados por relevancia (puede ser texto plano o JSON serializado). |
| relevance_filtered_documents_flag | INT          | Indicador/flag asociado al filtrado de documentos. |
| graph_feedback                 | INT            | Calificación o feedback sobre el grafo (puede ser booleano o escala). |
| graph_feedback_comment         | TEXT           | Comentario libre del usuario sobre el grafo. |
| relevance_analysis             | JSONB          | Análisis de relevancia en formato JSON. |
| relevance_chunks_used          | INT            | Número de chunks usados en la búsqueda. |
| synthesis                      | TEXT           | Texto de la síntesis generada por el modelo. |
| synthesis_length_words         | INT            | Número de palabras en la síntesis. |
| synthesis_length_chars         | INT            | Número de caracteres en la síntesis. |
| synthesis_feedback             | INT            | Calificación o feedback sobre la síntesis. |
| synthesis_feedback_comment     | TEXT           | Comentario libre del usuario sobre la síntesis. |
| rating                         | INT            | Calificación general del resultado. |
| comment                        | TEXT           | Comentario general del usuario. |
| contar                         | INT            | Contador auxiliar (por defecto 1, para tracking o agregación). |
| feedback_type                  | VARCHAR(64)    | Tipo de feedback (por ejemplo, "synthesis", "relevance"). |
| source                         | VARCHAR(64)    | Origen del feedback (por ejemplo, "web", "api"). |
| client_version                 | VARCHAR(64)    | Versión del cliente o frontend que envió el feedback. |


### Resumen de campos principales

La tabla `interactions` almacena el feedback y las interacciones de usuario, con los siguientes grupos de campos (y orden real en la base de datos):

1. **Identificación y sesión:**
   - `id` (SERIAL, PK)
   - `timestamp` (TIMESTAMP, default CURRENT_TIMESTAMP)
   - `user_email` (VARCHAR)
   - `session_id` (VARCHAR)
   - `ip_address` (VARCHAR)
2. **Consulta y contexto:**
   - `query` (TEXT)
   - `model_name_relevance` (VARCHAR)
   - `model_name_synthesis` (VARCHAR)
   - `relevance_filtered_collections` (TEXT)
   - `relevance_filtered_collections_flag` (INT)
   - `relevance_filtered_documents` (TEXT)
   - `relevance_filtered_documents_flag` (INT)
3. **Feedback de grafo:**
   - `graph_feedback` (INT)
   - `graph_feedback_comment` (TEXT)
4. **Análisis de relevancia/grafo:**
   - `relevance_analysis` (JSONB)
   - `relevance_chunks_used` (INT)
5. **Síntesis y feedback:**
   - `synthesis` (TEXT)
   - `synthesis_length_words` (INT)
   - `synthesis_length_chars` (INT)
   - `synthesis_feedback` (INT)
   - `synthesis_feedback_comment` (TEXT)
6. **Feedback general y metadatos:**
   - `rating` (INT)
   - `comment` (TEXT)
   - `contar` (INT, default 1)
   - `feedback_type` (VARCHAR)
   - `source` (VARCHAR)
   - `client_version` (VARCHAR)


**IMPORTANTE:** El backend espera que la base de datos PostgreSQL se llame `feedback975`. Si cambias el nombre, actualiza la variable `POSTGRES_DB` en el archivo `.env`.

Consulta el archivo [`DB_SCHEMA.md`](./DB_SCHEMA.md) para el SQL completo y la descripción detallada de cada campo.

## Estructura

- `app/` - Código fuente del backend (FastAPI)
- `schemas/` - Esquemas y catálogos JSON
- `scripts/` - Scripts auxiliares

## Requisitos
- Python 3.10+
- Elasticsearch (en ejecución y accesible)
- (Opcional) Entorno virtual Python

## Instalación

1. Instala las dependencias:
   ```bash
   pip install -r ../../requirements.txt
   ```

2. (Opcional) Activa tu entorno virtual:
   ```bash
   source ../../venv/bin/activate
   ```

## Ejecución

### Solo backend
```bash
bash start_api.sh
```
Esto levanta FastAPI en http://localhost:5555

### Backend + Frontend juntos
```bash
bash start_all.sh
```
Esto levanta el backend (puerto 5555) y el frontend (puerto 5173) en paralelo.

## Ejecución recomendada del backend

Para evitar problemas de compatibilidad con Elasticsearch y asegurar que los headers sean correctos, ejecuta SIEMPRE el backend usando:

```bash
cd backend
./start_api.sh
```

Esto configura automáticamente la variable de entorno `ELASTIC_CLIENT_APIVERSIONING=8` antes de lanzar FastAPI.

---

## Notas
- El frontend está en la carpeta `../frontend/`.
- Ajusta las variables de entorno y configuración según tu despliegue.

# Backend FastAPI – Memorias 975

## Arquitectura y Organización

- **`app/api/v1/endpoints/`**: Endpoints HTTP. Solo reciben parámetros, validan y delegan a servicios.
- **`app/services/`**: Lógica de negocio. Aquí va la integración con Elasticsearch, LLMs, procesamiento, etc.
- **`app/schemas/`** y **`app/models/`**: Modelos Pydantic para entrada/salida de datos.
- **`app/utils/`**: Utilidades y helpers.
- **`app/core/`**: Configuración y utilidades globales.
- **`app/db/`**: Conexión a bases de datos (ej. Elasticsearch).

## Ejemplo de flujo (búsqueda híbrida)

1. **El endpoint** recibe la petición y valida los parámetros:
   - Archivo: `app/api/v1/endpoints/search.py`
2. **Llama a la función de servicio** correspondiente:
   - Archivo: `app/services/search_service.py`
3. **El servicio** ejecuta la lógica (consulta a Elastic, embeddings, filtrado, etc.) y retorna un modelo Pydantic.
4. **El endpoint** devuelve la respuesta al frontend.

## Ejemplo de Endpoint y Servicio

### Endpoint
```python
@router.get("/", response_model=SearchResponse)
def search_endpoint(query: str, ...):
    """
    Realiza una búsqueda híbrida (texto + embeddings).
    """
    return simple_search(query, ...)
```

### Servicio
```python
def simple_search(query: str, ...):
    """
    Ejecuta la búsqueda híbrida en Elastic y embeddings.
    """
    # ... lógica ...
    return SearchResponse(results=...)
```

## Ejemplo de Modelo
```python
class SearchResult(BaseModel):
    id: str
    content: str
    page: Optional[int]
    # ...otros campos...

class SearchResponse(BaseModel):
    results: List[SearchResult]
```

## Buenas prácticas
- **No mezcles lógica de negocio en los endpoints.**
- **Documenta** cada endpoint y servicio con docstrings claros y ejemplos de uso.
- **Agrega tests** para los servicios críticos.
- **Actualiza este README** si cambias la arquitectura.

## Ejemplo de request/response

**Request:**
```
GET /search?query=justicia+transicional&llm_model=Azure+OpenAI+o3-mini&top_k=10
```

**Response:**
```json
{
  "results": [
    {"id": "abc123", "content": "...", "page": 5},
    ...
  ]
}
```

---

Para dudas o contribuciones, consulta la documentación interna o contacta al equipo de desarrollo.

---

## Push automático a GitHub usando el token del .env

Para subir tus cambios al repositorio remoto de GitHub usando el token almacenado en tu archivo `.env`, puedes usar el script:

```bash
bash scripts/git_push_token.sh "Mensaje de commit"
```

Este script:
- Lee el token y la URL del repo desde `backend/.env`.
- Realiza el commit y push de forma segura usando el token.
- No subas nunca el archivo `.env` a un repositorio público.

Si tienes problemas de permisos, revisa que tu token tenga permisos de escritura en el repositorio.
