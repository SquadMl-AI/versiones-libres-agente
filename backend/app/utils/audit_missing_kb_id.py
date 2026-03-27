# Script para auditar documentos sin kb_id en un índice de Elasticsearch
from elasticsearch import Elasticsearch
import os

ES_HOST = os.getenv("ELASTICSEARCH_HOST", "http://localhost:9200")
ES_USER = os.getenv("ES_USER", None)
ES_PASSWORD = os.getenv("ES_PASSWORD", None)
INDEX_NAME = os.getenv("INDEX_NAME", "ragflow_2a699818691611ef94690242ac120006")

client = Elasticsearch(
    hosts=[ES_HOST],
    basic_auth=(ES_USER, ES_PASSWORD) if ES_USER and ES_PASSWORD else None,
    verify_certs=False
)


def find_docs_missing_kb_id(index=INDEX_NAME, size=1000):
    query = {
        "query": {
            "bool": {
                "should": [
                    {"bool": {"must_not": [{"exists": {"field": "kb_id"}}]}},
                    {"term": {"kb_id": ""}}
                ]
            }
        },
        "size": size
    }
    resp = client.search(index=index, body=query)
    hits = resp["hits"]["hits"]
    print(f"Encontrados {len(hits)} documentos sin kb_id en el índice '{index}':")
    for h in hits:
        doc_name = h['_source'].get('docnm_kwd', 'N/A')
        page = h['_source'].get('page_num_int', 'N/A')
        print(f"ID: {h['_id']}, doc_name: {doc_name}, page: {page}")


if __name__ == "__main__":
    find_docs_missing_kb_id()