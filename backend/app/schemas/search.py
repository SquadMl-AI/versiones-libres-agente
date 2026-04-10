# app/schemas/search.py

from pydantic import BaseModel


class SearchResult(BaseModel):
    id: str
    title: str
    content: str
    collection: str | None = None
    document: str | None = None
    page: str | None = None
    score: float | None = None
    relevance: str | None = "Relevante"
    llm_summary: str | None = None  # Nuevo campo para mostrar el resumen LLM


class SearchResponse(BaseModel):
    results: list[SearchResult]
    graph: dict | None = None  # Siempre incluir el campo graph
    aggregations: dict | None = None  # Agregaciones/facetas de Elastic


# --- Para síntesis final ---
class SynthesisRequest(BaseModel):
    query: str
    llm_model: str
    results: list[SearchResult]
    relevance_categories: list[str] | None = ["Relevante"]
    user_email: str | None = None


class SynthesisResponse(BaseModel):
    synthesis: str


class FeedbackRequest(BaseModel):
    # Identificación y sesión
    user_email: str
    session_id: str | None = None
    ip_address: str | None = None

    # Consulta y contexto
    query: str
    model_name_relevance: str | None = None
    model_name_synthesis: str | None = None
    relevance_filtered_collections: str | None = None
    relevance_filtered_collections_flag: int | None = None
    relevance_filtered_documents: str | None = None
    relevance_filtered_documents_flag: int | None = None

    # Feedback de grafo
    graph_feedback: int | None = None
    graph_feedback_comment: str | None = None

    # Análisis de relevancia/grafo
    relevance_analysis: list | None = None
    relevance_chunks_used: int | None = None

    # Síntesis y feedback
    synthesis: str | None = None
    synthesis_length_words: int | None = None
    synthesis_length_chars: int | None = None
    synthesis_feedback: int | None = None
    synthesis_feedback_comment: str | None = None

    # Feedback general y metadatos
    rating: int | None = None
    comment: str | None = None
    contar: int = 1
    feedback_type: str | None = None
    source: str | None = None
    client_version: str | None = None
    has_feedback: bool | None = None  # Nuevo campo: indica si la interacción tiene feedback explícito
