# utils.py
import json
import logging
import os
import re
import sys
from dotenv import load_dotenv
from openai import AzureOpenAI
from nltk.corpus import stopwords
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.model_handlers import initialize_client, invoke_model  # noqa: E402
from app.prompts.summarize_chunk_prompts import SUMMARIZE_CHUNK_SYSTEM_PROMPT, SUMMARIZE_CHUNK_USER_PROMPT  # noqa: E402
from app.db.elastic import get_elastic_client  # noqa: E402

# Cargar variables de entorno
load_dotenv()

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Descargar recursos de NLTK si no están presentes
try:
    stopwords.words('spanish')
except LookupError:
    import nltk
    nltk.download('stopwords')
    nltk.download('punkt')

# --- Clientes y variables globales ---
ES_HOST = os.getenv("ELASTICSEARCH_HOST")
ES_USER = os.getenv("ES_USER")
ES_PASSWORD = os.getenv("ES_PASSWORD")
ES_ENDPOINT = os.getenv("ES_ENDPOINT")
ES_API_KEY = os.getenv("ES_API_KEY")
INDEX_NAME = os.getenv("INDEX_NAME")
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY")
EMBEDDING_ENDPOINT = os.getenv("EMBEDDING_ENDPOINT")

# Inicializar cliente de Elasticsearch
ES_CLIENT = get_elastic_client()

# Inicializar cliente de Azure OpenAI para embeddings
client_azure = AzureOpenAI(
    api_key=EMBEDDING_API_KEY,
    api_version="2023-05-15",
    azure_endpoint=EMBEDDING_ENDPOINT,
)


def get_datasets():
    """Returns a dictionary of all datasets."""
    return load_kb_id_to_name_map()


def get_dataset_documents(dataset_id: str):
    """
    Get all unique documents for a given dataset_id.
    """
    search_body = {
        "query": {
            "term": {
                "dataset_id.keyword": dataset_id
            }
        },
        "_source": ["document_id", "document_name"],
        "size": 10000
    }
    try:
        response = ES_CLIENT.search(index=INDEX_NAME, body=search_body)
        hits = response["hits"]["hits"]
        documents = {}
        for hit in hits:
            source = hit["_source"]
            doc_id = source.get("document_id")
            if doc_id and doc_id not in documents:
                documents[doc_id] = {
                    "document_id": doc_id,
                    "document_name": source.get("document_name", doc_id)
                }
        return list(documents.values())
    except Exception as e:
        logger.error(f"Error getting documents for dataset {dataset_id}: {e}")
        return []


def get_embedding(text):
    headers_emb = {"api-key": EMBEDDING_API_KEY, "Content-Type": "application/json"}
    data = {"input": text}
    try:
        response = requests.post(EMBEDDING_ENDPOINT, headers=headers_emb, json=data)
        if response.status_code == 200:
            return response.json()["data"][0]["embedding"]
        else:
            logger.error("Error al obtener embedding: " + response.text)
            return None
    except Exception as e:
        logger.error(f"Error al llamar a Azure OpenAI embeddings: {e}")
        return None


def clean_thinking(text):
    pattern = r"<thinking>.*?</thinking>"
    return re.sub(pattern, "", text, flags=re.DOTALL).strip()


def load_kb_id_to_name_map():
    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'schemas', 'kb_id_to_name.json')
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def hybrid_search_es(query, top_k=30, dataset_ids=None, document_ids=None, embedding_provider="azure", **kwargs):
    """
    Reemplazo: usa la búsqueda híbrida en Elasticsearch Cloud (KNN+texto).
    """
    import importlib.util
    import os
    import sys
    from app.utils.kb_catalog import get_kb_name_from_id  # noqa: E402

    # Cargar el módulo busqueda_escloud dinámicamente
    module_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'busqueda_escloud.py')
    spec = importlib.util.spec_from_file_location('busqueda_escloud', module_path)
    busqueda_escloud = importlib.util.module_from_spec(spec)
    sys.modules['busqueda_escloud'] = busqueda_escloud
    spec.loader.exec_module(busqueda_escloud)

    result = busqueda_escloud.hybrid_search_escloud(
        query, k=top_k, dataset_ids=dataset_ids, document_ids=document_ids,
        embedding_provider=embedding_provider
    )
    hits = result["hits"]
    aggregations = result.get("aggregations", {})

    # Adaptar a formato esperado por el resto de la app
    chunks = []
    for hit in hits:
        source = hit["_source"]

        def safe_str(val):
            if isinstance(val, list):
                return ", ".join(str(v) for v in val)
            if val is None:
                return ""
            return str(val)

        kb_id = safe_str(source.get("kb_id", "Sin Colección"))
        dataset_name = (
            get_kb_name_from_id(kb_id) if kb_id and kb_id != "Sin Colección" else "Sin Colección"
        )
        chunk = {
            "id": hit["_id"],
            "content": safe_str(source.get("content_with_weight", "")),
            "score": hit.get("_score", 0),
            "page": safe_str(source.get("page_num_int", "N/A")),
            "document_name": safe_str(source.get("docnm_kwd", "Desconocido")),
            "dataset_name": dataset_name,
            "kb_id": kb_id,
            "embedding": source.get("q_3072_vec")
        }
        # Añadir fragmentos resaltados si existen
        if "highlight_fragments" in hit:
            chunk["highlight_fragments"] = hit["highlight_fragments"]
        chunks.append(chunk)

    return {"chunks": chunks, "total": len(chunks), "aggregations": aggregations}


def summarize_chunk_streaming(chunk_info, user_query, provider="Azure OpenAI (o3-mini)"):
    client, model, base_url = initialize_client(provider)
    if not client:
        logger.error(f"Could not initialize model client for provider: {provider}")
        yield "Error: No se pudo inicializar el modelo."
        return

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

    full_response_content = ""
    try:
        stream = invoke_model(
            client, model, base_url, system_prompt, user_prompt,
            provider, max_tokens=1500, stream=True
        )
        for chunk in stream:
            content = chunk.choices[0].delta.content or ""
            full_response_content += content
            yield content
    except Exception as e:
        logger.error(f"Error during model invocation: {e}")
        yield "Error al generar el resumen."


def test_es_chunk_query():
    """
    Prueba una consulta directa a Elasticsearch para obtener un chunk/documento.
    Modifica 'test_query' o 'test_id' según tus datos reales.
    """
    test_query = {
        "query": {
            "match_all": {}
        },
        "size": 1
    }
    try:
        print("Ejecutando consulta de prueba a Elasticsearch...")
        response = ES_CLIENT.search(index=INDEX_NAME, body=test_query)
        print("Respuesta de Elasticsearch:")
        print(json.dumps(response, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error al consultar Elasticsearch: {e}")


if __name__ == "__main__":
    test_es_chunk_query()