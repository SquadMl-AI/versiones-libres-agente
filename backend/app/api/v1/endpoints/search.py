# app/api/v1/endpoints/search.py
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, Request
from app.services.search_service import simple_search, simple_search_progress_ws
from app.services.logging_service import log_interaction
from app.utils.kb_catalog import get_kb_name_from_id, load_kb_id_to_documents_map
from app.schemas.search import SearchResponse, FeedbackRequest

router = APIRouter()


@router.get("/documents_by_collection/{kb_id}")
def get_documents_for_collection(kb_id: str):
    """Devuelve los documentos para una colección específica."""
    catalog = load_kb_id_to_documents_map()
    documents = catalog.get(kb_id, [])
    return {"kb_id": kb_id, "documents": documents}


@router.get("/all_documents")
def get_all_documents():
    """Devuelve el catálogo completo de documentos por colección."""
    return load_kb_id_to_documents_map()


@router.get("/", response_model=SearchResponse)
@router.get("", response_model=SearchResponse)
def search_endpoint(
    query: str = Query(...),
    llm_model: str = Query(None),
    top_k: int = Query(20, description="Número de chunks a recuperar"),
    max_llm_chunks: int = Query(20, description="Chunks a analizar con LLM"),
    dataset_ids: list[str] = Query(None, description="IDs de colección a filtrar"),
    document_ids: list[str] = Query(None, description="IDs de documento a filtrar"),
    user_email: str = Query(None, description="Email del usuario para logging"),
    embedding_provider: str = Query("azure", description="Proveedor de embeddings: 'azure' u 'openai'")
):
    """
    Realiza una búsqueda híbrida (texto + embeddings).
    Parámetros:
      - query: Consulta del usuario.
      - llm_model: Modelo LLM a usar.
      - top_k: Número de chunks a recuperar.
      - max_llm_chunks: Chunks a analizar con LLM.
      - dataset_ids: IDs de colección a filtrar.
      - document_ids: IDs de documento a filtrar.
      - user_email: Email del usuario para logging.
      - embedding_provider: Proveedor de embeddings ('azure' u 'openai').
    Returns:
      dict con resultados relevantes.
    Ejemplo de request:30
      /search?query=justicia+transicional&llm_model=Azure+OpenAI+o3-mini&top_k=10&user_email=test@fiscalia.gov.co
    Ejemplo de response:
      {
        "results": [
          {"id": "abc123", "content": "...", "page": 5, ...},
          ...
        ]
      }
    """
    try:
        response = simple_search(
            query,
            llm_model=llm_model,
            top_k=top_k,
            max_llm_chunks=max_llm_chunks,
            user_email=user_email,
            dataset_ids=dataset_ids,
            document_ids=document_ids,
            embedding_provider=embedding_provider
        )
        # Forzamos conversión a dict para asegurar serialización JSON
        if hasattr(response, 'dict'):
            return response.dict()
        return response
    except Exception as e:
        import traceback
        return {"results": [], "error": str(e), "trace": traceback.format_exc()}


@router.websocket("/ws/search_progress")
async def search_progress_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        query = data.get("query")
        llm_model = data.get("llm_model")
        top_k = data.get("top_k", 20)
        max_llm_chunks = data.get("max_llm_chunks", 20)
        user_email = data.get("user_email")
        dataset_ids = data.get("dataset_ids")
        document_ids = data.get("document_ids")
        embedding_provider = data.get("embedding_provider", "azure")
        await simple_search_progress_ws(
            websocket, query, llm_model, top_k, max_llm_chunks, user_email,
            dataset_ids=dataset_ids, document_ids=document_ids,
            embedding_provider=embedding_provider
        )
    except WebSocketDisconnect:
        pass


@router.get("/kb_name/{kb_id}")
def get_kb_name(kb_id: str):
    """Devuelve el nombre legible de un kb_id usando el catálogo local."""
    name = get_kb_name_from_id(kb_id)
    return {"kb_id": kb_id, "name": name}


@router.post("/feedback")
def log_feedback(payload: FeedbackRequest, request: Request):
    """Logs user feedback for graph or synthesis, con rating de estrellas y comentario obligatorio si rating <= 3."""
    # Validación: comentario obligatorio si rating <= 3
    if payload.rating is not None and payload.rating <= 3 and (not payload.comment or payload.comment.strip() == ""):
        return {"status": "error", "detail": "Comentario obligatorio para calificaciones de 3 estrellas o menos."}

    # Obtener la IP real del request de forma robusta
    ip_address = request.client.host if request.client else None

    log_interaction(
        # Identificación y sesión
        user_email=payload.user_email,
        session_id=getattr(payload, 'session_id', None),
        ip_address=ip_address,

        # Consulta y contexto
        query=payload.query,
        model_name_relevance=getattr(payload, 'model_name_relevance', None),
        model_name_synthesis=getattr(payload, 'model_name_synthesis', None),
        relevance_filtered_collections=getattr(payload, 'relevance_filtered_collections', None),
        relevance_filtered_collections_flag=getattr(payload, 'relevance_filtered_collections_flag', None),
        relevance_filtered_documents=getattr(payload, 'relevance_filtered_documents', None),
        relevance_filtered_documents_flag=getattr(payload, 'relevance_filtered_documents_flag', None),

        # Feedback de grafo
        graph_feedback=getattr(payload, 'graph_feedback', None),
        graph_feedback_comment=getattr(payload, 'graph_feedback_comment', None),

        # Análisis de relevancia/grafo
        relevance_analysis=getattr(payload, 'relevance_analysis', None),
        relevance_chunks_used=getattr(payload, 'relevance_chunks_used', None),

        # Síntesis y feedback
        synthesis=getattr(payload, 'synthesis', None),
        synthesis_length_words=getattr(payload, 'synthesis_length_words', None),
        synthesis_length_chars=getattr(payload, 'synthesis_length_chars', None),
        synthesis_feedback=getattr(payload, 'synthesis_feedback', None),
        synthesis_feedback_comment=getattr(payload, 'synthesis_feedback_comment', None),

        # Feedback general y metadatos
        rating=payload.rating,
        comment=payload.comment,
        contar=getattr(payload, 'contar', 1),
        feedback_type=getattr(payload, 'feedback_type', None),
        source=getattr(payload, 'source', None),
        client_version=getattr(payload, 'client_version', None)
    )
    return {"status": "feedback logged"}
