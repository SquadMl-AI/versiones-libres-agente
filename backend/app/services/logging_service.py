import os
import uuid
import json
from datetime import datetime
import psycopg2
from psycopg2.extras import Json

# Cargar configuración desde .env
from dotenv import load_dotenv
# Carga explícita del .env en /backend/.env
BACKEND_ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../.env'))
load_dotenv(BACKEND_ENV_PATH)

PG_HOST = os.getenv('POSTGRES_HOST', 'localhost')
PG_PORT = os.getenv('POSTGRES_PORT', '5432')
PG_DB = os.getenv('POSTGRES_DB', 'sentencias_975')
PG_USER = os.getenv('POSTGRES_USER', 'postgres')
PG_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')


def _filter_relevance_analysis(relevance_analysis):
    """Filtra relevance_analysis para dejar solo los chunks analizados por el LLM."""
    if not (relevance_analysis and isinstance(relevance_analysis, list)):
        return None
    filtered = []
    for chunk in relevance_analysis:
        llm_sum = chunk.get("llm_summary", "")
        if (
            "Relevante" in llm_sum
            and "No Relevante" not in llm_sum
            and "No analizado" not in llm_sum
        ):
            filtered.append({
                "id": chunk.get("id"),
                "title": chunk.get("title"),
                "document": chunk.get("document"),
                "page": chunk.get("page"),
                "llm_summary": llm_sum
            })
    return filtered if filtered else None


def _compute_synthesis_lengths(synthesis, synthesis_length_words, synthesis_length_chars):
    """Calcula longitud de síntesis si no viene en el payload."""
    if synthesis:
        if synthesis_length_words is None:
            synthesis_length_words = len(synthesis.split())
        if synthesis_length_chars is None:
            synthesis_length_chars = len(synthesis)
    return synthesis_length_words, synthesis_length_chars


def _build_log_entry(log_id, timestamp, user_email, query, rating, comment,
                     graph_feedback, graph_feedback_comment, synthesis,
                     synthesis_feedback, synthesis_feedback_comment, relevance_analysis):
    """Construye el dict de entrada de log para el archivo de respaldo."""
    log_entry = {
        "id": log_id,
        "timestamp": timestamp.isoformat(),
        "user_email": user_email,
        "query": query,
        "rating": rating,
        "comment": comment,
    }
    if graph_feedback:
        log_entry["graph_feedback"] = graph_feedback
    if graph_feedback_comment:
        log_entry["graph_feedback_comment"] = graph_feedback_comment
    if synthesis:
        log_entry["synthesis"] = synthesis
    if synthesis_feedback:
        log_entry["synthesis_feedback"] = synthesis_feedback
    if synthesis_feedback_comment:
        log_entry["synthesis_feedback_comment"] = synthesis_feedback_comment
    if relevance_analysis and isinstance(relevance_analysis, list) and len(relevance_analysis) > 0:
        log_entry["relevance_analysis"] = relevance_analysis
    return log_entry


def _save_to_file(log_id, timestamp, user_email, query, rating, comment,
                  graph_feedback, graph_feedback_comment, synthesis,
                  synthesis_feedback, synthesis_feedback_comment, relevance_analysis):
    """Guarda la interacción en archivo plano como respaldo."""
    LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
    os.makedirs(LOG_DIR, exist_ok=True)
    LOG_FILE_PATH = os.path.join(LOG_DIR, "interactions.log")
    log_entry = _build_log_entry(
        log_id, timestamp, user_email, query, rating, comment,
        graph_feedback, graph_feedback_comment, synthesis,
        synthesis_feedback, synthesis_feedback_comment, relevance_analysis
    )
    print("\033[93m[LOG] Guardando feedback en archivo plano de respaldo:\033[0m")
    print(json.dumps(log_entry, ensure_ascii=False, indent=2))
    with open(LOG_FILE_PATH, "a") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


def _upsert_to_postgres(values):
    """Ejecuta el UPSERT en PostgreSQL."""
    upsert_sql = '''
        INSERT INTO interactions (
            user_email, session_id, ip_address,
            query, model_name_relevance, model_name_synthesis,
            relevance_filtered_collections, relevance_filtered_collections_flag,
            relevance_filtered_documents, relevance_filtered_documents_flag,
            graph_feedback, graph_feedback_comment,
            relevance_analysis, relevance_chunks_used,
            synthesis, synthesis_length_words, synthesis_length_chars,
            synthesis_feedback, synthesis_feedback_comment,
            rating, comment, contar, feedback_type, source, client_version,
            has_feedback
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_email, session_id, query)
        DO UPDATE SET
            ip_address = EXCLUDED.ip_address,
            model_name_relevance = EXCLUDED.model_name_relevance,
            model_name_synthesis = EXCLUDED.model_name_synthesis,
            relevance_filtered_collections = EXCLUDED.relevance_filtered_collections,
            relevance_filtered_collections_flag = EXCLUDED.relevance_filtered_collections_flag,
            relevance_filtered_documents = EXCLUDED.relevance_filtered_documents,
            relevance_filtered_documents_flag = EXCLUDED.relevance_filtered_documents_flag,
            graph_feedback = EXCLUDED.graph_feedback,
            graph_feedback_comment = EXCLUDED.graph_feedback_comment,
            relevance_analysis = EXCLUDED.relevance_analysis,
            relevance_chunks_used = EXCLUDED.relevance_chunks_used,
            synthesis = EXCLUDED.synthesis,
            synthesis_length_words = EXCLUDED.synthesis_length_words,
            synthesis_length_chars = EXCLUDED.synthesis_length_chars,
            synthesis_feedback = EXCLUDED.synthesis_feedback,
            synthesis_feedback_comment = EXCLUDED.synthesis_feedback_comment,
            rating = EXCLUDED.rating,
            comment = EXCLUDED.comment,
            contar = EXCLUDED.contar,
            feedback_type = EXCLUDED.feedback_type,
            source = EXCLUDED.source,
            client_version = EXCLUDED.client_version,
            has_feedback = EXCLUDED.has_feedback,
            timestamp = CURRENT_TIMESTAMP
    '''
    conn = psycopg2.connect(
        host=PG_HOST, port=PG_PORT, dbname=PG_DB, user=PG_USER, password=PG_PASSWORD
    )
    print("\033[92m[PG] Conexión a PostgreSQL exitosa.\033[0m")
    cur = conn.cursor()
    if len(values) != 26:
        print(
            f"\033[91m[PG][ERROR] La cantidad de valores enviados al INSERT es "
            f"{len(values)}, se esperaban 26.\033[0m"
        )
    print(f"[PG][DEBUG] Valores enviados al INSERT ({len(values)}): {values}")
    cur.execute(upsert_sql, values)
    conn.commit()
    cur.close()
    conn.close()
    print("\033[92m[PG] Registro de feedback insertado/actualizado correctamente en PostgreSQL.\033[0m")


def log_interaction(
    # Identificación y sesión
    user_email: str,
    session_id: str = None,
    ip_address: str = None,

    # Consulta y contexto
    query: str = None,
    model_name_relevance: str = None,
    model_name_synthesis: str = None,
    relevance_filtered_collections: str = None,
    relevance_filtered_collections_flag: int = None,
    relevance_filtered_documents: str = None,
    relevance_filtered_documents_flag: int = None,

    # Feedback de grafo
    graph_feedback: int = None,
    graph_feedback_comment: str = None,

    # Análisis de relevancia/grafo
    relevance_analysis: list = None,
    relevance_chunks_used: int = None,

    # Síntesis y feedback
    synthesis: str = None,
    synthesis_length_words: int = None,
    synthesis_length_chars: int = None,
    synthesis_feedback: int = None,
    synthesis_feedback_comment: str = None,

    # Feedback general y metadatos
    rating: int = None,
    comment: str = None,
    contar: int = 1,
    feedback_type: str = None,
    source: str = None,
    client_version: str = None
):
    """
    Registra la interacción del usuario en la base de datos PostgreSQL.
    Guarda: timestamp, user_email, session_id, ip_address, query, model_name_relevance,
    model_name_synthesis, graph_feedback, synthesis, synthesis_feedback,
    relevance_analysis (si aplica), y comentarios de insatisfacción si los hay.
    relevance_analysis debe ser una lista de dicts con los campos: id, score, relevance, llm_summary
    """
    # Si no hay nada relevante, no registrar
    if not (
        query or graph_feedback or synthesis or synthesis_feedback
        or (relevance_analysis and len(relevance_analysis) > 0)
    ):
        print("\033[93m[LOG] No se registró interacción: payload vacío o irrelevante.\033[0m")
        return

    log_id = str(uuid.uuid4())
    timestamp = datetime.now()

    # Nuevos campos: session_id, ip_address, model_name_relevance, model_name_synthesis
    # Si no se pasan, intentar obtener de variables de entorno (para compatibilidad)
    session_id = session_id or os.environ.get('SESSION_ID')
    ip_address = ip_address or os.environ.get('USER_IP')
    model_name_relevance = model_name_relevance or os.environ.get('MODEL_NAME_RELEVANCE')
    model_name_synthesis = model_name_synthesis or os.environ.get('MODEL_NAME_SYNTHESIS')

    # Calcular longitud de síntesis si no viene
    synthesis_length_words, synthesis_length_chars = _compute_synthesis_lengths(
        synthesis, synthesis_length_words, synthesis_length_chars
    )

    # Filtrar relevance_analysis para dejar solo los chunks analizados por el LLM
    relevance_analysis = _filter_relevance_analysis(relevance_analysis)

    # Mostrar el payload recibido para depuración
    print("\033[96m[LOG] Payload recibido para log_interaction:\033[0m")
    print(json.dumps({
        # Identificación y sesión
        "user_email": user_email,
        "session_id": session_id,
        "ip_address": ip_address,

        # Consulta y contexto
        "query": query,
        "model_name_relevance": model_name_relevance,
        "model_name_synthesis": model_name_synthesis,
        "relevance_filtered_collections": relevance_filtered_collections,
        "relevance_filtered_collections_flag": relevance_filtered_collections_flag,
        "relevance_filtered_documents": relevance_filtered_documents,
        "relevance_filtered_documents_flag": relevance_filtered_documents_flag,

        # Feedback de grafo
        "graph_feedback": graph_feedback,
        "graph_feedback_comment": graph_feedback_comment,

        # Análisis de relevancia/grafo
        "relevance_analysis": relevance_analysis,
        "relevance_chunks_used": relevance_chunks_used,

        # Síntesis y feedback
        "synthesis": synthesis,
        "synthesis_length_words": synthesis_length_words,
        "synthesis_length_chars": synthesis_length_chars,
        "synthesis_feedback": synthesis_feedback,
        "synthesis_feedback_comment": synthesis_feedback_comment,

        # Feedback general y metadatos
        "rating": rating,
        "comment": comment,
        "contar": contar,
        "feedback_type": feedback_type,
        "source": source,
        "client_version": client_version
    }, ensure_ascii=False, indent=2))

    # Calcular si hay feedback explícito
    has_feedback = any([
        synthesis_feedback is not None,
        graph_feedback is not None,
        rating is not None,
        comment,
        synthesis_feedback_comment,
        graph_feedback_comment
    ])

    values = [
        user_email,                   # 1
        session_id,                   # 2
        ip_address,                   # 3
        query,                        # 4
        model_name_relevance,         # 5
        model_name_synthesis,         # 6
        relevance_filtered_collections,       # 7
        relevance_filtered_collections_flag,  # 8
        relevance_filtered_documents,         # 9
        relevance_filtered_documents_flag,    # 10
        graph_feedback,               # 11
        graph_feedback_comment,       # 12
        Json(relevance_analysis) if relevance_analysis else None,  # 13
        relevance_chunks_used,        # 14
        synthesis,                    # 15
        synthesis_length_words,       # 16
        synthesis_length_chars,       # 17
        synthesis_feedback,           # 18
        synthesis_feedback_comment,   # 19
        rating,                       # 20
        comment,                      # 21
        contar,                       # 22
        feedback_type,                # 23
        source,                       # 24
        client_version,               # 25
        has_feedback                  # 26
    ]

    try:
        _upsert_to_postgres(values)
    except Exception as e:
        print(f"\033[91m[PG][ERROR] Fallo al insertar/actualizar feedback en PostgreSQL: {e}\033[0m")
        _save_to_file(
            log_id, timestamp, user_email, query, rating, comment,
            graph_feedback, graph_feedback_comment, synthesis,
            synthesis_feedback, synthesis_feedback_comment, relevance_analysis
        )