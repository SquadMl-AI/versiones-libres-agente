## Esquema actual de la base de datos `feedback975`

### Tabla: `interactions`

```sql
CREATE TABLE interactions (
    id SERIAL PRIMARY KEY, -- Identificador único autoincremental
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Fecha y hora de registro
    user_email VARCHAR(255), -- Correo del usuario que envía el feedback
    session_id VARCHAR(255), -- ID de sesión del usuario (puede ser null)
    ip_address VARCHAR(64), -- IP desde donde se envía el feedback
    query TEXT, -- Consulta original del usuario
    model_name_relevance VARCHAR(128), -- Nombre del modelo usado para relevancia
    model_name_synthesis VARCHAR(128), -- Nombre del modelo usado para síntesis
    relevance_filtered_collections TEXT, -- Colecciones filtradas por relevancia (texto o JSON serializado)
    relevance_filtered_collections_flag INT, -- Flag asociado a filtrado de colecciones
    relevance_filtered_documents TEXT, -- Documentos filtrados por relevancia (texto o JSON serializado)
    relevance_filtered_documents_flag INT, -- Flag asociado a filtrado de documentos
    graph_feedback INT, -- Calificación o feedback sobre el grafo (1-5, booleano, etc.)
    graph_feedback_comment TEXT, -- Comentario libre sobre el grafo
    relevance_analysis JSONB, -- Análisis de relevancia (estructura JSON)
    relevance_chunks_used INT, -- Número de chunks usados en la búsqueda
    synthesis TEXT, -- Texto de la síntesis generada
    synthesis_length_words INT, -- Cantidad de palabras en la síntesis
    synthesis_length_chars INT, -- Cantidad de caracteres en la síntesis
    synthesis_feedback INT, -- Calificación o feedback sobre la síntesis
    synthesis_feedback_comment TEXT, -- Comentario libre sobre la síntesis
    rating INT, -- Calificación general (1-5, etc.)
    comment TEXT, -- Comentario general del usuario
    contar INT DEFAULT 1, -- Contador auxiliar (por defecto 1)
    feedback_type VARCHAR(64), -- Tipo de feedback ("synthesis", "relevance", etc.)
    source VARCHAR(64), -- Origen del feedback ("web", "api", etc.)
    client_version VARCHAR(64), -- Versión del cliente/frontend
    has_feedback BOOLEAN DEFAULT FALSE, -- Indica si la interacción tiene feedback explícito del usuario
    UNIQUE(user_email, session_id, query)
);

```

---

### Métricas y visualización temporal

La aplicación expone métricas agregadas y una línea de tiempo de interacciones a través del endpoint `/api/v1/dashboard/metrics`. Entre los datos expuestos se incluye:

- **Evolución de interacciones (últimos 30 días):**
  - El backend entrega un arreglo de objetos `{ date, count }` que representa la cantidad de interacciones por día.
  - Este dato se utiliza en el frontend para graficar una línea de tiempo (gráfico de líneas) que permite visualizar tendencias de uso y picos de actividad.
  - Además, se muestra una tabla detallada con los mismos datos para referencia.

**Ejemplo de estructura JSON:**

```json
{
  "evolution_last_30_days": [
    { "date": "2025-07-01", "count": 12 },
    { "date": "2025-07-02", "count": 18 },
    ...
  ],
  ...otros campos de métricas...
}
```

El campo `timestamp` de la tabla `interactions` es la fuente para calcular esta evolución temporal.

---

#### Descripción de los campos

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
| has_feedback                   | BOOLEAN        | Indica si la interacción tiene feedback explícito del usuario (TRUE si el usuario calificó o comentó, FALSE si solo realizó la búsqueda). |
```

## Descripción de campos

- **id**: Identificador único autoincremental de la interacción.
- **timestamp**: Fecha y hora en que se registró la interacción.
- **user_email**: Correo electrónico del usuario (puede ser anonimizable o hash).
- **session_id**: Identificador de sesión para agrupar interacciones de un mismo usuario.
- **ip_address**: Dirección IP del usuario.
- **query**: Consulta original realizada por el usuario.
- **model_name_relevance**: Nombre del modelo usado para la etapa de relevancia.
- **model_name_synthesis**: Nombre del modelo usado para la síntesis.
- **relevance_filtered_collections**: Colecciones filtradas por el modelo de relevancia.
- **relevance_filtered_collections_flag**: Flag binario (1/0) indicando si hubo filtrado de colecciones.
- **relevance_filtered_documents**: Documentos filtrados por el modelo de relevancia.
- **relevance_filtered_documents_flag**: Flag binario (1/0) indicando si hubo filtrado de documentos.
- **graph_feedback**: Calificación (1-5 estrellas) dada al grafo generado.
- **graph_feedback_comment**: Comentario obligatorio si la calificación de grafo es 3 o menor.
- **relevance_analysis**: Análisis detallado de relevancia/grafo (estructura flexible, JSON).
- **relevance_chunks_used**: Número de fragmentos/chunks usados en la etapa de relevancia/grafo.
- **synthesis**: Texto completo de la síntesis generada por el modelo.
- **synthesis_length_words**: Número de palabras de la síntesis.
- **synthesis_length_chars**: Número de caracteres de la síntesis.
- **synthesis_feedback**: Calificación (1-5 estrellas) dada a la síntesis.
- **synthesis_feedback_comment**: Comentario obligatorio si la calificación de síntesis es 3 o menor.
- **rating**: Calificación general (opcional, para compatibilidad con versiones anteriores).
- **comment**: Comentario general (opcional, para compatibilidad con versiones anteriores).
- **contar**: Siempre 1, útil para agregaciones rápidas en reportes.
- **feedback_type**: Tipo de feedback registrado ("synthesis", "graph", etc.).
- **source**: Origen del feedback (ejemplo: "web", "api").
- **client_version**: Versión del cliente/frontend que envió el feedback.
- **has_feedback**: Valor booleano que indica si la interacción tiene feedback explícito del usuario (`TRUE` si el usuario calificó o dejó comentario, `FALSE` si solo realizó la búsqueda sin calificar ni comentar).

---

> **Nota:** Este esquema está alineado con el modelo Pydantic `FeedbackRequest` y la lógica de logging en el backend. Si se agregan o modifican campos, actualizar este documento y los modelos correspondientes.
