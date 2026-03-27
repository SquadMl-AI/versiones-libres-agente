import sys
import os

# Añadir el directorio raíz del proyecto al sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import json  # noqa: E402
from app.db.elastic import get_elastic_client  # noqa: E402
from dotenv import load_dotenv  # noqa: E402


# Cargar variables de entorno
load_dotenv()

# Paths
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCHEMAS = os.path.join(BASE, "schemas")
DOC_CATALOG_PATH = os.path.join(SCHEMAS, "kb_id_to_documents.json")
INDEX_NAME = os.getenv("INDEX_NAME", "search_engine_v1")


def update_document_catalog():
    """Crea un catálogo de kb_id a documentos."""
    es = get_elastic_client()
    if not es:
        print("Error: No se pudo conectar a Elasticsearch.")
        return

    # Query para obtener todos los documentos y agrupar por kb_id
    query = {
        "size": 0,
        "aggs": {
            "collections": {
                "terms": {"field": "kb_id", "size": 1000},
                "aggs": {
                    "documents": {
                        "terms": {"field": "docnm_kwd", "size": 1000}
                    }
                }
            }
        }
    }

    try:
        response = es.search(index=INDEX_NAME, body=query)
    except Exception as e:
        print(f"Error al consultar Elasticsearch: {e}")
        return

    doc_catalog = {}
    if 'aggregations' in response:
        for collection_bucket in response['aggregations']['collections']['buckets']:
            kb_id = collection_bucket['key']
            documents = [doc_bucket['key'] for doc_bucket in collection_bucket['documents']['buckets']]
            doc_catalog[kb_id] = documents
    else:
        print("No se encontraron agregaciones en la respuesta de Elasticsearch.")
        print("Respuesta de Elasticsearch:")
        print(json.dumps(response, indent=2))

    with open(DOC_CATALOG_PATH, "w") as f:
        json.dump(doc_catalog, f, indent=2)

    print(f"Catálogo de documentos guardado en {DOC_CATALOG_PATH}")


if __name__ == "__main__":
    update_document_catalog()