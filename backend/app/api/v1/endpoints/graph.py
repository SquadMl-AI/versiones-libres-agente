# backend/app/api/v1/endpoints/graph.py
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from app.services.search_category_service import SearchCategoryChunks
from app.services.graph_service import plot_interactive_graph, build_initial_search_graph
from typing import Optional
from pydantic import BaseModel

search = SearchCategoryChunks()
router = APIRouter()


class Request(BaseModel):
    query: Optional[str] = None


@router.post("/test-vis-network")
def test_vis_network(request: Request):
    # query = "Cuál fue la pena impuesta inicialmente y cuál fue la pena final acumulada tras la apelación?"
    # Solo el primer chunk
    search_result = search.classification_pipeline_endpoint(request.query)
    # Construir grafo solo con el primer chunk
    if not search_result:
        return HTMLResponse("<h2>No se encontraron resultados para la consulta.</h2>")

    G = build_initial_search_graph(search_result.model_dump())

    return {"content": plot_interactive_graph(G)}
