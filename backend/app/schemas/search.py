# app/schemas/search.py
from pydantic import BaseModel
from typing import List, Optional


class SearchResult(BaseModel):
    id: str
    title: str
    content: str
    collection: Optional[str] = None
    document: Optional[str] = None
    page: Optional[str] = None
    score: Optional[float] = None
    relevance: Optional[str] = "Relevante"
    llm_summary: Optional[str] = None  # Nuevo campo para mostrar el resumen LLM


class SearchResponse(BaseModel):
    results: List[SearchResult]
    graph: Optional[dict] = None  # Siempre incluir el campo graph
    aggregations: Optional[dict] = None  # Agregaciones/facetas de Elastic


# --- Para síntesis final ---
class SynthesisRequest(BaseModel):
    query: str
    llm_model: str
    results: List[SearchResult]
    relevance_categories: Optional[List[str]] = ["Relevante"]
    user_email: Optional[str] = None


class SynthesisResponse(BaseModel):
    synthesis: str


class FeedbackRequest(BaseModel):
    # Identificación y sesión
    user_email: str
    session_id: Optional[str] = None
    ip_address: Optional[str] = None

    # Consulta y contexto
    query: str
    model_name_relevance: Optional[str] = None
    model_name_synthesis: Optional[str] = None
    relevance_filtered_collections: Optional[str] = None
    relevance_filtered_collections_flag: Optional[int] = None
    relevance_filtered_documents: Optional[str] = None
    relevance_filtered_documents_flag: Optional[int] = None

    # Feedback de grafo
    graph_feedback: Optional[int] = None
    graph_feedback_comment: Optional[str] = None

    # Análisis de relevancia/grafo
    relevance_analysis: Optional[list] = None
    relevance_chunks_used: Optional[int] = None

    # Síntesis y feedback
    synthesis: Optional[str] = None
    synthesis_length_words: Optional[int] = None
    synthesis_length_chars: Optional[int] = None
    synthesis_feedback: Optional[int] = None
    synthesis_feedback_comment: Optional[str] = None

    # Feedback general y metadatos
    rating: Optional[int] = None
    comment: Optional[str] = None
    contar: int = 1
    feedback_type: Optional[str] = None
    source: Optional[str] = None
    client_version: Optional[str] = None
    has_feedback: Optional[bool] = None  # Nuevo campo: indica si la interacción tiene feedback explícito
