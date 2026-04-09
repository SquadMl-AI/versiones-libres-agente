"""
Búsqueda híbrida en Elasticsearch Cloud (KNN + texto) para Memorias 975.
Requiere variables de entorno:
- ES_ENDPOINT
- ES_API_KEY
- INDEX_NAME
- EMBEDDING_ENDPOINT
- EMBEDDING_API_KEY

Extrae embeddings con Azure OpenAI y consulta Elasticsearch Cloud usando API Key.
"""

# Importaciones necesarias
import os  # Para interactuar con el sistema operativo, como leer variables de entorno.
import requests  # Para realizar peticiones HTTP a la API de Azure OpenAI.
from elasticsearch import Elasticsearch  # Cliente oficial de Elasticsearch para Python.
from elasticsearch.exceptions import RequestError  # Para manejar errores específicos de Elasticsearch.
from dotenv import load_dotenv  # Para cargar variables de entorno desde un archivo .env.
import json  # Para trabajar con datos en formato JSON.
import logging  # Para registrar mensajes de información y errores.

# Configuración del logging para mostrar mensajes informativos en la consola.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carga las variables de entorno desde un archivo .env si existe.
load_dotenv()

# --- Variables de Entorno ---
# Lee las credenciales y configuraciones desde las variables de entorno.
# Si ES_ENDPOINT no está, intenta con ELASTICSEARCH_HOST por retrocompatibilidad.
ES_ENDPOINT = os.getenv("ES_ENDPOINT") or os.getenv("ELASTICSEARCH_HOST")
ES_API_KEY = os.getenv("ES_API_KEY")  # API Key para autenticarse con Elasticsearch.
INDEX_NAME = os.getenv("INDEX_NAME")  # Nombre del índice en Elasticsearch a consultar.
EMBEDDING_ENDPOINT = os.getenv("EMBEDDING_ENDPOINT")  # URL del servicio de embeddings de Azure OpenAI.
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY")  # API Key para el servicio de embeddings.
VECTOR_FIELD = "q_3072_vec"  # Nombre del campo en Elasticsearch que contiene los vectores (embeddings).
TEXT_FIELD = "content_ltks"  # Nombre del campo que contiene el texto para búsqueda de texto completo.

# Leer también las variables de entorno de OpenAI directo
OPENAI_EMBEDDING_API_KEY = os.getenv("OPENAI_EMBEDDING_API_KEY")
OPENAI_EMBEDDING_ENDPOINT = os.getenv("OPENAI_EMBEDDING_ENDPOINT")

# --- Cliente de Elasticsearch ---
# Inicializa el cliente de Elasticsearch con la URL del endpoint y la API Key.
# Este objeto se usará para todas las comunicaciones con el clúster de Elasticsearch.
es_client = Elasticsearch(ES_ENDPOINT, api_key=ES_API_KEY)


def get_embedding(text, provider="azure"):
    """
    Obtiene embeddings usando Azure OpenAI o OpenAI directo según el proveedor.

    Args:
        text (str): El texto de entrada para el cual se generará el embedding.
        provider (str): El proveedor de embeddings a utilizar ("azure" u "openai").

    Returns:
        list: Un vector (lista de floats) que representa el embedding del texto.

    Raises:
        Exception: Si la petición a la API de Azure falla.
    """
    if provider == "openai":
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_EMBEDDING_API_KEY}"}
        data = {"input": text, "model": "text-embedding-3-large"}
        endpoint = OPENAI_EMBEDDING_ENDPOINT
    else:
        headers = {"Content-Type": "application/json", "api-key": EMBEDDING_API_KEY}
        data = {"input": text}
        endpoint = EMBEDDING_ENDPOINT
    try:
        response = requests.post(endpoint, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["data"][0]["embedding"]
    except requests.RequestException as e:
        logger.error(f"Error al obtener embedding ({provider}): {e}")
        raise Exception(f"No se pudo obtener el embedding: {str(e)}")


def _build_must_filters(dataset_ids, document_ids):
    """Construye los filtros must para las consultas de Elasticsearch."""
    must_filters = []
    if dataset_ids:
        must_filters.append({"terms": {"kb_id": dataset_ids}})
    if document_ids:
        must_filters.append({"terms": {"docnm_kwd": document_ids}})
    return must_filters


def _process_hits(hits):
    """Filtra y enriquece los hits con fragmentos resaltados."""
    filtered_hits = []
    for hit in hits:
        if hit["_source"].get(TEXT_FIELD):
            if "highlight" in hit:
                hit["highlight_fragments"] = hit["highlight"].get(TEXT_FIELD, [])
            filtered_hits.append(hit)
    return filtered_hits


def _process_aggregations(aggs):
    """Procesa las agregaciones de la respuesta de Elasticsearch."""
    aggregations = {}
    if aggs:
        for agg_name in ["by_collection", "by_document", "by_year"]:
            buckets = aggs.get(agg_name, {}).get("buckets", [])
            aggregations[agg_name] = [{"key": b["key"], "doc_count": b["doc_count"]} for b in buckets]
    return aggregations


def _execute_es_search(query_body):
    """Ejecuta una búsqueda en Elasticsearch y maneja los errores."""
    try:
        return es_client.search(index=INDEX_NAME, body=query_body)
    except RequestError as e:
        logger.error(f"Error en la consulta a Elasticsearch: {e}")
        raise Exception(f"Error en la búsqueda: {e.info.get('error', {}).get('reason', 'Desconocido')}")
    except Exception as e:
        logger.error(f"Error inesperado en la búsqueda: {e}")
        raise Exception(f"Error inesperado: {str(e)}")


def hybrid_search_escloud(query, k=30, dataset_ids=None, document_ids=None, embedding_provider="azure", debug=False):
    """
    Realiza una búsqueda híbrida (BM25 + KNN) en Elasticsearch Cloud usando RRF (Reciprocal Rank Fusion).
    Combina la búsqueda de texto tradicional (BM25) con la búsqueda por similitud vectorial (KNN).

    Args:
        query (str): El texto de la consulta del usuario.
        k (int): El número máximo de resultados a devolver.
        dataset_ids (list, optional): Lista de IDs de "datasets" para filtrar los resultados.
        document_ids (list, optional): Lista de IDs de documentos para filtrar los resultados.
        embedding_provider (str, optional): Proveedor de embeddings a utilizar ("azure" u "openai").
        debug (bool, optional): Si es True, imprime la consulta enviada a Elasticsearch.

    Returns:
        list: Una lista de "hits" (documentos encontrados) ordenados por relevancia según RRF.

    Raises:
        Exception: Si ocurre un error durante la consulta a Elasticsearch.
    """
    # 1. Generar el embedding para el texto de la consulta.
    vector = get_embedding(query, provider=embedding_provider)

    # 2. Configurar los filtros para la consulta.
    must_filters = _build_must_filters(dataset_ids, document_ids)

    # 3. Ajustar `num_candidates` para la búsqueda KNN.
    # `num_candidates` es el número de vecinos que se consideran en cada shard.
    # Debe ser >= k. Se aumenta un 50% para tener un margen, sin superar 10,000.
    num_candidates = min(max(int(k * 1.5), k), 10000)

    # 4. Construir la consulta RRF (Reciprocal Rank Fusion) usando la sintaxis moderna de retrievers.
    rrf_query = {
        "retriever": {
            "rrf": {
                "retrievers": [
                    {
                        "standard": {
                            "query": {
                                "multi_match": {
                                    "query": query,
                                    "fields": [TEXT_FIELD]
                                }
                            },
                            "filter": must_filters if must_filters else []
                        }
                    },
                    {
                        "knn": {
                            "field": VECTOR_FIELD,
                            "query_vector": vector,
                            "k": k,
                            "num_candidates": num_candidates,
                            "filter": must_filters if must_filters else []
                        }
                    }
                ],
                "rank_window_size": k,
                "rank_constant": 20
            }
        },
        "size": k,
        "highlight": {
            "fields": {
                TEXT_FIELD: {}
            }
        },
        "aggs": {
            "by_collection": {"terms": {"field": "kb_id", "size": 20}},
            "by_document": {"terms": {"field": "docnm_kwd", "size": 20}},
            "by_year": {"terms": {"field": "year", "size": 20}}
        }
    }

    # Si el modo debug está activado, imprime la consulta completa en formato JSON.
    if debug:
        logger.debug(f"Consulta RRF: {json.dumps(rrf_query, indent=2)}")

    # 5. Ejecutar la consulta en Elasticsearch.
    res = _execute_es_search(rrf_query)

    # 6. Procesar los resultados y agregaciones.
    # Extrae la lista de "hits" de la respuesta.
    hits = res.body["hits"]["hits"] if hasattr(res, 'body') else res["hits"]["hits"]
    filtered_hits = _process_hits(hits)

    # Procesar agregaciones si existen
    aggs = res.body.get("aggregations") if hasattr(res, 'body') else res.get("aggregations")
    aggregations = _process_aggregations(aggs)

    # Si el modo debug está activado, informa cuántos resultados se obtuvieron y las agregaciones
    if debug:
        logger.debug(f"Resultados obtenidos: {len(filtered_hits)} hits")
        logger.debug(f"Agregaciones: {json.dumps(aggregations, indent=2)}")

    return {"hits": filtered_hits, "aggregations": aggregations}


def text_only_search_escloud(query, k=30, dataset_ids=None, document_ids=None, debug=False):
    """
    Realiza una búsqueda solo de texto (BM25) en Elasticsearch Cloud.
    Esta función es útil cuando no se requiere la búsqueda por similitud vectorial.

    Args:
        query (str): El texto de la consulta.
        k (int): El número de resultados a devolver.
        dataset_ids (list, optional): IDs de "datasets" para filtrar.
        document_ids (list, optional): IDs de documentos para filtrar.
        debug (bool, optional): Activa logs de depuración.

    Returns:
        list: Una lista de "hits" ordenados por relevancia (puntuación BM25).
    """
    # 1. Configurar los filtros, igual que en la búsqueda híbrida.
    must_filters = _build_must_filters(dataset_ids, document_ids)

    # 2. Construir la consulta de búsqueda de texto.
    es_query = {
        "bool": {
            "should": [
                # La cláusula "should" indica una preferencia. Aquí, buscamos el texto en el campo principal.
                # `boost: 2` le da más importancia a los aciertos en este campo.
                {"multi_match": {"query": query, "fields": [TEXT_FIELD], "boost": 2}}
            ],
            # `minimum_should_match: 1` requiere que al menos una de las cláusulas "should" coincida.
            "minimum_should_match": 1,
            # `must` requiere que todas las condiciones (filtros) se cumplan.
            "must": must_filters if must_filters else []
        }
    }
    # Cuerpo completo de la petición a Elasticsearch, incluyendo el bloque de highlighting nativo.
    body = {
        "size": k,  # Limita el número de resultados.
        "query": es_query,
        "highlight": {
            "fields": {
                TEXT_FIELD: {}
            },
            # Opcional: puedes ajustar los tags de resaltado si lo deseas
            # "pre_tags": ["<mark>"],
            # "post_tags": ["</mark>"]
        }
    }

    # Si el modo debug está activado, imprime la consulta.
    if debug:
        logger.debug(f"Consulta de texto: {json.dumps(body, indent=2)}")

    # 3. Ejecutar la consulta.
    res = _execute_es_search(body)

    # 4. Procesar los resultados.
    hits = res.body["hits"]["hits"] if hasattr(res, 'body') else res["hits"]["hits"]
    filtered_hits = _process_hits(hits)

    if debug:
        logger.debug(f"Resultados obtenidos: {len(filtered_hits)} hits")

    return filtered_hits
