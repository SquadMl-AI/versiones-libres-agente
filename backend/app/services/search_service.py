import asyncio
import logging
import re
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import networkx as nx

from app.db.elastic import get_elastic_client
from app.model_handlers import initialize_client, invoke_model
from app.prompts.summarize_chunk_prompts import (
    SUMMARIZE_CHUNK_SYSTEM_PROMPT,
    SUMMARIZE_CHUNK_USER_PROMPT
)
from app.prompts.final_synthesis_prompts import (
    FINAL_SYNTHESIS_SYSTEM_PROMPT,
    FINAL_SYNTHESIS_USER_PROMPT
)
from app.schemas.search import SearchResponse, SearchResult, SynthesisRequest, SynthesisResponse
from app.services.graph_service import build_initial_search_graph, build_final_hierarchy_graph
from app.utils_helpers import clean_thinking, hybrid_search_es
from .logging_service import log_interaction

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))


def summarize_chunk_llm_backend(
    chunk_info,
    user_query,
    provider="Azure OpenAI (gpt-4.1-mini)"
):
    client, model, base_url = initialize_client(provider)
    if not client and provider not in ["Google (Gemini-2.0-Flash)", "Azure OpenAI (gpt-4.1-mini)"]:
        return "Error: No se pudo inicializar el modelo.", "No Relevante"
    system_prompt = SUMMARIZE_CHUNK_SYSTEM_PROMPT.format(user_query=user_query)
    user_prompt = SUMMARIZE_CHUNK_USER_PROMPT.format(
        user_query=user_query,
        dataset_name=chunk_info.get('dataset_name', 'Sin Colección'),
        document_name=chunk_info.get('document_name', 'Sin Documento'),
        page=chunk_info.get('page', 'N/A'),
        chunk_id=chunk_info.get('id', 'N/A'),
        similarity=chunk_info.get('score', 'N/A'),
        content=chunk_info.get('content', 'Sin contenido')
    )
    full_response = invoke_model(
        client, model, base_url, system_prompt, user_prompt,
        provider, max_tokens=1500, stream=False
    )
    cleaned = clean_thinking(full_response)
    classification_match = re.search(
        r"Clasificación: (Relevante|Relevancia Indeterminada|No Relevante)",
        cleaned
    )
    classification = classification_match.group(1) if classification_match else "No Relevante"
    return cleaned, classification


def simple_search(
    query: str,
    llm_model: str = None,
    top_k: int = 300,
    max_llm_chunks: int = 30,
    user_email: str = None,
    dataset_ids: list = None,
    document_ids: list = None,
    embedding_provider: str = "azure"
):
    """
    Ejecuta la búsqueda híbrida en Elastic y embeddings.
    Args:
        query (str): Consulta del usuario.
        llm_model (str): Modelo LLM a usar.
        top_k (int): Número de resultados a recuperar.
        max_llm_chunks (int): Chunks a analizar con LLM.
    Returns:
        SearchResponse: Resultados estructurados.
    Ejemplo de uso:
        response = simple_search("justicia transicional", llm_model="Azure OpenAI (o3-mini)", top_k=10)
    """
    try:
        print(f"[DEBUG] Llamando a hybrid_search_es con query: {query} y top_k: {top_k} "
              f"y embedding_provider: {embedding_provider}")
        data = hybrid_search_es(
            query,
            top_k=top_k,
            dataset_ids=dataset_ids,
            document_ids=document_ids,
            embedding_provider=embedding_provider
        )
        chunks = data["chunks"]
        aggregations = data.get("aggregations", {})

        if not chunks:
            print("[DEBUG] No se encontraron chunks tras hybrid_search_es.")
            print("[DEBUG] Respuesta vacía: { 'results': [], 'graph': None, 'aggregations': {}}")
            return SearchResponse(results=[], graph=None, aggregations=aggregations)

        relevance_provider = "Azure OpenAI (gpt-4.1-mini)"
        if llm_model in ["Azure OpenAI (o3-mini)"]:
            relevance_provider = "Azure OpenAI (o3-mini)"
        elif llm_model in ["Azure OpenAI (o4-mini)"]:
            relevance_provider = "Azure OpenAI (o4-mini)"

        llm_chunks = chunks[:max_llm_chunks]
        results_futures = []
        with ThreadPoolExecutor() as executor:
            for chunk in llm_chunks:
                future = executor.submit(
                    summarize_chunk_llm_backend, chunk, query, relevance_provider
                )
                results_futures.append(future)
            for i, future in enumerate(results_futures):
                summary, relevance = future.result()
                llm_chunks[i]["relevance"] = relevance
                llm_chunks[i]["llm_summary"] = summary

        for chunk in chunks[max_llm_chunks:]:
            chunk["relevance"] = "No Analizado"
            chunk["llm_summary"] = "No analizado por LLM (fuera del top seleccionable)"

        results = [
            SearchResult(
                id=c.get("id", f"chunk_{i+1}"),
                title=f"Chunk {i+1}",
                content=c.get("content", ""),
                collection=c.get("dataset_name", ""),
                document=c.get("document_name", ""),
                page=str(c.get("page", "")),
                score=c.get("score", 0),
                relevance=c.get("relevance", "No Analizado"),
                llm_summary=c.get("llm_summary", "")
            )
            for i, c in enumerate(chunks)
        ]

        print(f"[DEBUG] {len(results)} resultados procesados.")
        print(f"[INFO] Chunks recuperados: {len(chunks)} | "
              f"Chunks analizados por LLM: {len(llm_chunks)}")

        # Construir el grafo con todos los chunks recuperados
        graph = build_initial_search_graph(chunks)
        graph_json = nx.node_link_data(graph)

        print("[DEBUG] Grafo construido.")
        return SearchResponse(results=results, graph=graph_json, aggregations=aggregations)

    except Exception:
        logging.exception("Error in simple_search (hybrid_search_es)")
        return SearchResponse(results=[], graph=None, aggregations={})


# ---------- Funciones auxiliares para simple_search_progress_ws ----------
async def _send_progress_update(websocket, idx, total, chunk_result):
    """Envía una actualización de progreso al WebSocket."""
    await websocket.send_json({
        "type": "progress",
        "current": idx + 1,
        "total": total,
        "chunk_id": chunk_result.get("chunk_id"),
        "relevance": chunk_result.get("relevance"),
        "llm_summary": chunk_result.get("llm_summary")
    })


async def _send_error_progress(websocket, idx, total, exc):
    """Envía un error de progreso al WebSocket."""
    await websocket.send_json({
        "type": "progress",
        "current": idx + 1,
        "total": total,
        "chunk_id": None,
        "relevance": "Error",
        "llm_summary": f"Error: {exc}"
    })


def _build_graph_from_results(results, query):
    """Construye el grafo final a partir de los resultados."""
    try:
        G = build_final_hierarchy_graph(
            results,
            query=query,
            classifications_to_include=["Relevante", "Relevancia Indeterminada", "No Relevante"]
        )
        nodes = []
        for n, data in G.nodes(data=True):
            node = {"id": str(n)}
            node.update(data)
            node.setdefault("type", "chunk")
            node.setdefault("label", str(n))
            if node["type"] in ["chunk", "document"]:
                node.setdefault("full_name", node.get("full_name", str(n)))
                node.setdefault("summary", data.get("summary", ""))
                node.setdefault("content", data.get("content", ""))
                node.setdefault("score", data.get("score", ""))
                node.setdefault("classification", data.get("classification", ""))
                node.setdefault("dataset_name", data.get("dataset_name", ""))
                node.setdefault("document_name", data.get("document_name", ""))
                node.setdefault("page", data.get("page", ""))
            nodes.append(node)

        edges = []
        edge_count = 0
        for u, v, data in G.edges(data=True):
            u_str, v_str = str(u), str(v)
            if u_str and v_str:
                edges.append({
                    "id": f"rel_{edge_count}",
                    "type": "RELATES_TO",
                    "from": u_str,
                    "to": v_str,
                    "properties": {"from": u_str, "to": v_str, **data}
                })
                edge_count += 1

        # Asegurar que todos los nodos referenciados estén presentes
        node_ids = set(str(n["id"]) for n in nodes)
        referenced_ids = set(e["from"] for e in edges).union(set(e["to"] for e in edges))
        missing_ids = referenced_ids - node_ids
        for mid in missing_ids:
            nodes.append({"id": mid, "label": mid, "type": "unknown"})

        # Asegurar nodo central/root
        all_from = set(e["from"] for e in edges if "from" in e)
        all_to = set(e["to"] for e in edges if "to" in e)
        root_candidates = [f for f in all_from if f not in all_to]
        for root_id in root_candidates:
            if root_id and not any(n["id"] == root_id for n in nodes):
                nodes.append({"id": root_id, "label": root_id, "type": "root"})

        nodes = [n for n in nodes if n["id"]]
        return {"nodes": nodes, "edges": edges}
    except Exception:
        logging.exception("Error al construir el grafo de relevancia")
        return None


async def simple_search_progress_ws(
    websocket,
    query,
    llm_model,
    top_k=300,
    max_llm_chunks=30,
    user_email: str = None,
    dataset_ids: list = None,
    document_ids: list = None,
    embedding_provider: str = "azure"
):
    try:
        print(f"[DEBUG][WS] Recibido en simple_search_progress_ws: query={query}, "
              f"llm_model={llm_model}, top_k={top_k}, max_llm_chunks={max_llm_chunks}, "
              f"user_email={user_email}, dataset_ids={dataset_ids}, document_ids={document_ids}, "
              f"embedding_provider={embedding_provider}")
        print("[DEBUG][WS] Llamando a hybrid_search_es...")
        data = hybrid_search_es(
            query,
            top_k=top_k,
            page_size=100,
            dataset_ids=dataset_ids,
            document_ids=document_ids,
            embedding_provider=embedding_provider
        )
        print("[DEBUG][WS] hybrid_search_es terminó de ejecutarse.")
        print(f"[DEBUG][WS] hybrid_search_es retornó {len(data['chunks']) if 'chunks' in data else 'NO chunks'} chunks.")
        chunks = data["chunks"]

        if not chunks:
            print("[DEBUG][WS] No se encontraron chunks tras hybrid_search_es. Enviando 'done' vacío.")
            await websocket.send_json({"type": "done", "results": [], "graph": None})
            return

        relevance_provider = "Azure OpenAI (o3-mini)"
        if llm_model in ["Azure OpenAI (gpt-4.1-mini)"]:
            relevance_provider = "Azure OpenAI (gpt-4.1-mini)"
        elif llm_model in ["Azure OpenAI (o4-mini)"]:
            relevance_provider = "Azure OpenAI (o4-mini)"

        llm_chunks = chunks[:max_llm_chunks]

        # --- PROCESAMIENTO PARALELO ---
        def process_chunk(chunk):
            summary, relevance = summarize_chunk_llm_backend(chunk, query, relevance_provider)
            chunk["relevance"] = relevance
            chunk["llm_summary"] = summary
            return {
                "chunk_id": chunk.get("id"),
                "relevance": relevance,
                "llm_summary": summary
            }

        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(process_chunk, chunk): i for i, chunk in enumerate(llm_chunks)}
            for idx, future in enumerate(as_completed(futures)):
                try:
                    result = future.result()
                    await _send_progress_update(websocket, idx, len(llm_chunks), result)
                except Exception as exc:
                    await _send_error_progress(websocket, idx, len(llm_chunks), exc)
                await asyncio.sleep(0)  # Cede control al event loop

        for chunk in chunks[max_llm_chunks:]:
            chunk["relevance"] = "No Analizado"
            chunk["llm_summary"] = "No analizado por LLM (fuera del top seleccionable)"

        results = [
            SearchResult(
                id=c.get("id", f"chunk_{i+1}"),
                title=f"Chunk {i+1}",
                content=c.get("content", ""),
                collection=c.get("dataset_name", ""),
                document=c.get("document_name", ""),
                page=str(c.get("page", "")),
                score=c.get("score", 0),
                relevance=c.get("relevance", "No Analizado"),
                llm_summary=c.get("llm_summary", None)
            )
            for i, c in enumerate(chunks)
        ]

        graph = _build_graph_from_results(results, query)

        response_data = {
            "type": "done",
            "results": [r.dict() for r in results],
            "graph": graph
        }
        await websocket.send_json(response_data)

    except Exception as e:
        print(f"[ERROR][WS] Excepción en simple_search_progress_ws: {e}")
        logging.exception("Error in simple_search_progress_ws (hybrid_search_es)")
        await websocket.send_json({"type": "error", "message": str(e)})


# ---------- Funciones auxiliares para synthesize_final ----------
def _build_references(payload, cats):
    """Construye la cadena de referencias para la síntesis."""
    references = ""
    for i, r in enumerate(payload.results, 1):
        if getattr(r, "relevance", "Relevante") in cats:
            references += (
                f"--- Referencia procesada {i} ---\n"
                f"Metadata:\n"
                f"  - Colección: {getattr(r, 'collection', 'Sin Colección')}\n"
                f"  - Documento: {getattr(r, 'document', 'Sin Documento')}\n"
                f"  - Página: {getattr(r, 'page', 'N/A')}\n"
                f"  - Chunk ID: {getattr(r, 'id', 'N/A')}\n"
                f"  - Score: {getattr(r, 'score', 'N/A')}\n"
                f"Resumen LLM:\n{getattr(r, 'llm_summary', 'Sin resumen')}\n\n"
            )
    return references


def synthesize_final(payload: SynthesisRequest, stream: bool = False):
    """
    Genera una síntesis automática de los resultados seleccionados usando LLM.
    Args:
        payload (SynthesisRequest): Incluye query, modelo, resultados y categorías de relevancia.
    Returns:
        SynthesisResponse: Texto de síntesis generado.
    """
    MAX_LLM_CHUNKS = 100
    if not payload.results or len(payload.results) == 0:
        return SynthesisResponse(
            synthesis="No se seleccionaron fragmentos para sintetizar. Por favor, selecciona al menos un chunk relevante."
        )
    if len(payload.results) > MAX_LLM_CHUNKS:
        payload.results = payload.results[:MAX_LLM_CHUNKS]

    try:
        print(f"[SYNTHESIS DEBUG] stream={stream} | total_chunks_seleccionados={len(payload.results)}")
    except Exception:
        pass

    cats = payload.relevance_categories or ["Relevante"]
    filtered_chunks = [r for r in payload.results if getattr(r, "relevance", "Relevante") in cats]
    try:
        print(f"[SYNTHESIS DEBUG] Chunks tras filtrar por relevancia {cats}: "
              f"{len(filtered_chunks)} IDs: {[getattr(r, 'id', None) for r in filtered_chunks]}")
    except Exception:
        pass

    references = _build_references(payload, cats)

    system_prompt = FINAL_SYNTHESIS_SYSTEM_PROMPT.format(classifications=", ".join(cats))
    user_prompt = FINAL_SYNTHESIS_USER_PROMPT.format(
        user_query=payload.query,
        classifications=", ".join(cats),
        references=references
    )

    llm_model = payload.llm_model or "Azure OpenAI (gpt-4.1)"
    client, model, base_url = initialize_client(llm_model)
    if not client and llm_model not in ["Google (Gemini-2.0-Flash)", "Azure OpenAI (o3-mini)"]:
        return SynthesisResponse(synthesis=f"Error: No se pudo inicializar el modelo {llm_model}.")

    if stream:
        return invoke_model(
            client, model, base_url, system_prompt, user_prompt,
            llm_model, max_tokens=4000, stream=True, synthesis_stream=True
        )
    else:
        full_response = invoke_model(
            client, model, base_url, system_prompt, user_prompt,
            llm_model, max_tokens=4000, stream=False
        )
        synthesis = clean_thinking(full_response)
        if payload.user_email:
            log_interaction(user_email=payload.user_email, query=payload.query, synthesis=synthesis)
        return SynthesisResponse(synthesis=synthesis)