# backend/conftest.py
"""
Conftest raíz del backend.
Se ejecuta ANTES de la recolección de tests, lo que permite mockear
módulos pesados de Azure SDK que no están instalados en el entorno de CI.
"""

import sys
from unittest.mock import MagicMock

# ──────────────────────────────────────────────────────────────────────
# Mockear módulos de Azure SDK a nivel de sys.modules ANTES de que
# pytest recolecte los archivos de test (y sus imports a nivel de módulo).
# Esto se ejecuta en el momento de carga de conftest, no como fixture.
# ──────────────────────────────────────────────────────────────────────
_MODULES_TO_MOCK = [
    # Azure Search SDK
    "azure",
    "azure.search",
    "azure.search.documents",
    "azure.search.documents.indexes",
    "azure.search.documents.indexes.models",
    "azure.search.documents.models",
    # Azure OpenAI / LangChain
    "langchain_openai",
    "openai",
    # Azure Document Intelligence
    "azure.ai",
    "azure.ai.formrecognizer",
    # Azure Blob Storage
    "azure.storage",
    "azure.storage.blob",
    # Azure Core
    "azure.core",
    "azure.core.exceptions",
    "azure.core.credentials",
    # Base de datos
    "pymongo",
    "pymongo.errors",
    # Otras dependencias pesadas
    "fitz",
    "numpy",
    "pandas",
]

for _mod in _MODULES_TO_MOCK:
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()


import os  # noqa: E402

# Variables de entorno necesarias para que los módulos no exploten al importarse
_ENV_VARS = {
    "AZURE_OPENAI_ENDPOINT": "https://fake-openai.azure.com",
    "AZURE_OPENAI_API_KEY": "fake-api-key",
    "AZURE_OPENAI_CHAT_MODEL_41": "gpt-4.1",
    "AZURE_OPENAI_CHAT_API_VERSION_41": "2024-01-01",
    "AZURE_OPENAI_CHAT_MODEL_41MINI": "gpt-4.1-mini",
    "AZURE_OPENAI_CHAT_API_VERSION_41MINI": "2024-01-01",
    "AZURE_OPENAI_EMBEDDING_MODEL": "text-embedding-ada-002",
    "AZURE_OPENAI_EMBEDDING_API_VERSION": "2024-01-01",
    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "embedding-deployment",
    "AZURE_AI_SEARCH_ENDPOINT": "https://fake-search.azure.com",
    "AZURE_AI_SEARCH_API_KEY": "fake-search-key",
    "AZURE_BLOB_STORAGE_CONNECTION_STRING": "DefaultEndpointsProtocol=https;AccountName=fake",
    "AZURE_BLOB_STORAGE_CONTAINER_NAME": "fake-container",
    "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT": "https://fake-doc.azure.com",
    "AZURE_DOCUMENT_INTELLIGENCE_API_KEY": "fake-doc-key",
    "AZURE_COSMOSDB_ENDPOINT": "mongodb://fake:fake@fake.mongo.cosmos.azure.com:10255/?ssl=true",
    "AZURE_COSMOSDB_DATABASE_NAME": "fake_db",
    "AZURE_COSMOSDB_COLLECTION_NAME": "fake_collection",
}

for key, value in _ENV_VARS.items():
    os.environ.setdefault(key, value)
