import os
import uuid
import pytest
from pathlib import Path
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

# Cargar .env desde backend/
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)


@pytest.fixture(scope="module")
def es_client():
    """
    Cliente Elasticsearch listo para integración real.
    - Hace skip si no hay entorno configurado
    - NO crea infraestructura
    """

    ES_HOST = os.getenv("ELASTICSEARCH_HOST")
    ES_API_KEY = os.getenv("ES_API_KEY")
    ES_USER = os.getenv("ES_USER")
    ES_PASSWORD = os.getenv("ES_PASSWORD")
    INDEX_NAME = os.getenv("INDEX_NAME")

    # Skip controlado (clave para entornos sin config)
    if not ES_HOST or not INDEX_NAME:
        pytest.skip("Entorno de Elasticsearch no configurado")

    if not (ES_API_KEY or (ES_USER and ES_PASSWORD)):
        pytest.skip("Credenciales de Elasticsearch no configuradas")

    # Normalizar host
    hosts = [h.strip() for h in ES_HOST.split(",") if h.strip()]
    hosts = [
        h if h.startswith(("http://", "https://")) else f"https://{h}"
        for h in hosts
    ]

    # Cliente
    if ES_API_KEY:
        client = Elasticsearch(
            hosts=hosts,
            api_key=ES_API_KEY,
            verify_certs=True
        )
    else:
        client = Elasticsearch(
            hosts=hosts,
            basic_auth=(ES_USER, ES_PASSWORD),
            verify_certs=True
        )

    # 🔌 Validar conexión
    if not client.ping():
        pytest.fail("No se pudo conectar a Elasticsearch")

    # Validar índice existente
    if not client.indices.exists(index=INDEX_NAME):
        pytest.fail(f"El índice '{INDEX_NAME}' no existe")

    return client, INDEX_NAME


@pytest.mark.integration
def test_es_index_and_search_flow(es_client):
    """
    Flujo real:
    1. Indexar documento
    2. Refrescar índice
    3. Buscar documento
    4. Validar consistencia
    5. Limpiar
    """

    client, index_name = es_client

    # Documento único
    doc_id = f"test-{uuid.uuid4()}"
    doc_body = {
        "content": "documento de prueba pytest elasticsearch",
        "source": "pytest"
    }

    try:
        # Indexar
        index_response = client.index(
            index=index_name,
            id=doc_id,
            document=doc_body
        )

        assert index_response["result"] in ("created", "updated")

        # Refrescar
        client.indices.refresh(index=index_name)

        # Buscar
        search_response = client.search(
            index=index_name,
            query={
                "match": {
                    "content": "prueba"
                }
            }
        )

        hits = search_response["hits"]["hits"]

        # Validaciones
        assert isinstance(hits, list)
        assert len(hits) > 0

        retrieved_ids = [hit["_id"] for hit in hits]
        assert doc_id in retrieved_ids

    finally:
        # Cleanup
        try:
            client.delete(index=index_name, id=doc_id)
            client.indices.refresh(index=index_name)
        except Exception as cleanup_error:
            print(f"[WARN] Cleanup falló: {cleanup_error}")
