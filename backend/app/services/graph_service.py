# backend/app/services/graph_service.py
import networkx as nx
from pyvis.network import Network
import re


def build_initial_search_graph(results, query=None):
    """
    Construye un grafo dirigido con la estructura:
    Raíz ("Resultados Búsqueda") -> Colección -> Documento -> Chunk,
    usando la nueva estructura de chunks clasificados.
    """
    G = nx.DiGraph()
    G.add_node("Resultados Búsqueda", type="root", level=0, label="Resultados Búsqueda", title="Raíz de la búsqueda")

    # Estructura: {colección: {documento: [chunks...]}}
    structure = {}
    chunks = results.get("high_score_categorized_chunks", [])

    for chunk in chunks:
        coll = chunk.get("folder", "Sin Colección")
        doc = chunk.get("document_name", "Sin Documento")
        structure.setdefault(coll, {}).setdefault(doc, []).append(chunk)

    # Usamos el score más alto para los colores
    max_score = max(chunk.get("reranker_score", 0) for chunk in chunks) if chunks else 1

    def score_to_color(score, max_score):
        fraction = score / max_score if max_score > 0 else 0
        if fraction < 0.33:
            return "#FF0000"  # rojo
        elif fraction < 0.66:
            return "#FFFF00"  # amarillo
        else:
            return "#00FF00"  # verde

    for coll, docs in structure.items():
        G.add_node(coll, type="collection", level=1, label=coll)
        G.add_edge("Resultados Búsqueda", coll)
        for doc, doc_chunks in docs.items():
            G.add_node(doc, type="document", level=2, label=doc)
            G.add_edge(coll, doc)
            for chunk in doc_chunks:
                # Nodo del chunk: texto corto o el ID, más metadatos útiles
                chunk_id = chunk.get("chunk id", "")
                resumen = chunk.get("resumen_llm", "") or chunk.get("content", "")[:100]
                color = score_to_color(chunk.get("reranker_score", 0), max_score)
                categoria = chunk.get("categoria", "Sin categoría")
                label = f"{categoria}: {chunk_id[:8]}"
                G.add_node(
                    chunk_id,
                    type="chunk",
                    level=3,
                    label=label,
                    color=color,
                    resumen_llm=resumen,
                    page_numbers=chunk.get("page_numbers", []),
                    categoria=categoria,
                    document_name=doc,
                    folder=coll
                )
                G.add_edge(doc, chunk_id)
    return G


def _get_chunk_color(relevance):
    """Devuelve el color correspondiente a la relevancia de un chunk."""
    if relevance == "Relevante":
        return "#4CAF50"  # Verde
    elif relevance == "Relevancia Indeterminada":
        return "#FFF9C4"  # Amarillo claro
    elif relevance == "No Relevante":
        return "#F44336"  # Rojo
    return "#9E9E9E"  # Gris por defecto para 'No Analizado'


def _get_chunk_label_page(page):
    """Extrae la página de etiqueta a partir del campo page de un chunk."""
    if isinstance(page, list) and len(page) > 0:
        return str(page[0])
    elif isinstance(page, str) and ',' in page:
        return page.split(',')[0].strip()
    return str(page)


def _sort_chunk_key(c):
    """Clave de ordenamiento para chunks por número de página."""
    page_val = getattr(c, 'page', '0')
    if isinstance(page_val, list):
        page_val = page_val[0] if page_val else '0'
    page_str = str(page_val)
    match = re.search(r'\d+', page_str)
    if match:
        return int(match.group(0))
    return 0


def _add_chunk_node(G, chunk, doc):
    """Añade un nodo de chunk al grafo con todos sus atributos."""
    chunk_node_id = getattr(chunk, 'id', None) or id(chunk)
    relevance = getattr(chunk, 'relevance', 'No Analizado')
    color = _get_chunk_color(relevance)

    tooltip = (
        f"Página: {getattr(chunk, 'page', 'N/A')}\n"
        f"Score: {getattr(chunk, 'score', 0):.2f}\n"
        f"Relevancia: {relevance}\n"
        f"Colección: {getattr(chunk, 'collection', 'Sin Colección')}\n"
        f"KB_ID: {getattr(chunk, 'kb_id', 'N/A')}"
    )
    summary = getattr(chunk, 'llm_summary', '')
    if summary and 'KB_ID:' not in summary:
        summary = summary + f"\nKB_ID: {getattr(chunk, 'kb_id', 'N/A')}"

    page = getattr(chunk, 'page', 'N/A')
    label_page = _get_chunk_label_page(page)

    G.add_node(
        chunk_node_id,
        type="chunk",
        level=4,
        label=f"Pág. {label_page}",
        title=tooltip,
        tooltip=tooltip,
        summary=summary,
        content=getattr(chunk, 'content', ''),
        classification=relevance,
        page=getattr(chunk, 'page', 'N/A'),
        score=getattr(chunk, 'score', 0),
        document=getattr(chunk, 'document', 'Sin Documento'),
        collection=getattr(chunk, 'collection', 'Sin Colección'),
        kb_id=getattr(chunk, 'kb_id', 'N/A'),
        color=color
    )
    return chunk_node_id


def _connect_chunks_sequentially(G, doc_id, sorted_chunks):
    """Conecta chunks secuencialmente por grupo de relevancia al grafo."""
    chunks_by_relevance = {}
    for chunk in sorted_chunks:
        relevance = getattr(chunk, 'relevance', 'No Analizado')
        chunks_by_relevance.setdefault(relevance, []).append(chunk)

    for relevance, chunks_in_group in chunks_by_relevance.items():
        prev_chunk_node_id = None
        for chunk in chunks_in_group:
            chunk_node_id = getattr(chunk, 'id', None) or id(chunk)
            if prev_chunk_node_id is None:
                G.add_edge(doc_id, chunk_node_id, title="")
            else:
                G.add_edge(
                    prev_chunk_node_id, chunk_node_id,
                    type="sequential", title=f"Secuencia: {relevance}"
                )
            prev_chunk_node_id = chunk_node_id


def build_final_hierarchy_graph(chunks, query=None, classifications_to_include=None):
    """
    Construye el grafo jerárquico final para la visualización.
    Todos los chunks se incluyen sin filtrar por categoría.
    Los nodos de documento y colección SIEMPRE se conservan si tienen al menos un chunk.
    Si un documento o colección no tiene ningún chunk, se oculta.
    """
    G = nx.DiGraph()

    # Nodo raíz: la consulta
    query_id = f"query_{query}"
    G.add_node(
        query_id,
        type="query",
        level=0,
        label=query,
        title=f"Consulta: {query}",
        shape="diamond",
        color={"background": "black", "border": "white"},
        size=25
    )

    # Nodo "Sentencias Ley 975"
    root_id = "Sentencias Ley 975"
    G.add_node(
        root_id,
        type="root",
        level=1,
        label=root_id,
        title=root_id,
        shape="star",
        color={"background": "white", "border": "black"},
    )
    G.add_edge(query_id, root_id, title="")

    # Agrupar por colección y documento todos los chunks
    structure = {}
    for chunk in chunks:
        coll = getattr(chunk, 'collection', 'Sin Colección')
        doc = getattr(chunk, 'document', 'Sin Documento')
        structure.setdefault(coll, {}).setdefault(doc, []).append(chunk)

    # Solo agregar colecciones y documentos si tienen al menos un chunk
    for coll, docs in structure.items():
        coll_id = f"collection_{coll}"
        G.add_node(coll_id, type="collection", level=2, label=coll, title=f"Colección: {coll}")
        G.add_edge(root_id, coll_id, title="")

        for doc, doc_chunks in docs.items():
            doc_id = f"document_{doc}"
            G.add_node(doc_id, type="document", level=3, label=doc, title=f"Documento: {doc}")
            G.add_edge(coll_id, doc_id, title="")

            sorted_chunks = sorted(doc_chunks, key=_sort_chunk_key)

            for chunk in sorted_chunks:
                _add_chunk_node(G, chunk, doc)

            _connect_chunks_sequentially(G, doc_id, sorted_chunks)

    return G


def _get_node_style(node_type, data):
    """Devuelve shape, color y size según el tipo de nodo."""
    font_size = 12
    shape = "ellipse"
    color = data.get("color", "#cccccc")
    size = data.get("size", 20)

    if node_type == "collection":
        shape = "box"
        color = "#3bd5df"
        size = 32
    elif node_type == "root":
        shape = "star"
        color = "#4378db"
        size = 38
    elif node_type == "query":
        shape = "diamond"
        color = "#000000"
        size = 30
    elif node_type == "document":
        shape = "triangle"
        color = "#ffb847"
        size = 28
        font_size = 11
    elif node_type == "chunk":
        clase = data.get("categoria", "").lower() or data.get("classification", "").lower()
        if clase == "relevante":
            color = "#68B66B"
        elif clase == "relevancia indeterminada":
            color = "#FFC107"
        elif clase == "no relevante":
            color = "#BDBDBD"
        elif clase == "no analizado":
            color = "#9E9E9E"
        else:
            color = "#E0E0E0"
        shape = "dot"
        size = 20

    return shape, color, size, font_size


def plot_interactive_graph(G, height="80vh", width="100%"):
    net = Network(height=height, width=width, directed=True, notebook=True)
    for node, data in G.nodes(data=True):
        node_type = data.get("type", "chunk")
        shape, color, size, font_size = _get_node_style(node_type, data)

        net.add_node(
            node,
            label=data.get("label", str(node)),
            title=data.get("title", ""),  # tooltip
            color=color,
            level=data.get("level"),
            shape=shape,
            size=size,
            font={"size": font_size}
        )
    for u, v, edata in G.edges(data=True):
        net.add_edge(u, v, **edata)

    net.set_options("""
        {
        "nodes": {"borderWidth": 2, "shadow": {"enabled": true, "size": 5, "x": 2, "y": 2}},
        "edges": {"smooth": false},
        "physics": {
            "enabled": true,
            "forceAtlas2Based": {
            "gravitationalConstant": -80,
            "centralGravity": 0.01,
            "springLength": 450,
            "springConstant": 0.08
            },
            "maxVelocity": 50,
            "solver": "forceAtlas2Based",
            "timestep": 0.35,
            "stabilization": {"enabled": true, "iterations": 1000}
        },
        "interaction": {"dragNodes": true, "dragView": true, "zoomView": true, "tooltipDelay": 200},
        "configure": {"enabled": false}
        }
    """)
    return net.generate_html()
