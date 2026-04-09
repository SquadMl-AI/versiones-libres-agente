# app/db/elastic.py

from elasticsearch import Elasticsearch
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))


def get_elastic_client():
    import logging
    host = os.getenv("ELASTICSEARCH_HOST")
    if not host or host.strip() == "":
        raise ValueError("ELASTICSEARCH_HOST environment variable is not set or empty.")
    if host and not host.startswith("http"):
        host = f"http://{host}"
    user = os.getenv("ES_USER")
    password = os.getenv("ES_PASSWORD")
    api_key = os.getenv("ES_API_KEY")
    logging.info(f"Connecting to Elasticsearch at {host} with user '{user}'")
    try:
        es_kwargs = {
            "headers": {
                "Accept": "application/vnd.elasticsearch+json; compatible-with=8",
                "Content-Type": "application/vnd.elasticsearch+json; compatible-with=8"
            },
            "hosts": [host]
        }
        if api_key:
            es_kwargs["api_key"] = api_key
        elif user and password:
            es_kwargs["http_auth"] = (user, password)
        client = Elasticsearch(**es_kwargs)
        # Prueba de conexión
        try:
            info = client.info()
            version = info.get('version', {}).get('number', 'desconocida')
            print(f"\033[92m[ES] Elasticsearch conectado: versión {version}\033[0m")
        except Exception as es_err:
            print(f"\033[91m[ES] Error al conectar con Elasticsearch: {es_err}\033[0m")
        logging.info("Elasticsearch client initialized (no connection test at init).")
        return client
    except Exception:
        logging.exception("Failed to initialize Elasticsearch client")
        raise
