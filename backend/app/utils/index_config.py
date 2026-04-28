import sys

sys.path.append("../utils")

from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchField,
    SearchFieldDataType,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)

# ----------------------------------------------------------------
# Crear los campos (fields)


def create_fields():
    fields_index = [
        SimpleField(
            name="doc_id",
            type=SearchFieldDataType.String,
            key=True,
        ),
        SimpleField(name="kb_id", type=SearchFieldDataType.String, retrievable=True, filterable=True),
        SimpleField(
            name="docnm_kwd",
            type=SearchFieldDataType.String,
            retrievable=True,
        ),
        SimpleField(name="docnm", type=SearchFieldDataType.String, retrievable=True, filterable=True),
        SimpleField(
            name="docnm_tks",
            type=SearchFieldDataType.String,
            retrievable=True,
        ),
        SimpleField(name="bloque", type=SearchFieldDataType.String, retrievable=True, filterable=True),
        SimpleField(name="group_id", type=SearchFieldDataType.String, retrievable=True, filterable=True),
        SearchField(
            name="content",
            type=SearchFieldDataType.String,
            searchable=True,
            filterable=True,
            sortable=False,
            facetable=False,
        ),
        SearchField(
            name="content_ltks",
            type=SearchFieldDataType.String,
            searchable=True,
            filterable=True,
            sortable=False,
            facetable=False,
        ),
        SimpleField(
            name="page_number",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Int32),
            retrievable=True,
        ),
        SearchField(
            name="embedded_content_ltks",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=3072,
            vector_search_profile_name="HnswProfile",
        ),
    ]

    return fields_index


# ----------------------------------------------------------------
# Configuración de búsqueda vectorial
def create_vectorsearch():
    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name="Hnswconfig",
                kind="hnsw",
                parameters={
                    "metric": "cosine",
                    "m": 8,
                    "ef_construction": 400,
                    "efSearch": 500,
                },
            )
        ],
        profiles=[VectorSearchProfile(name="HnswProfile", algorithm_configuration_name="Hnswconfig")],
    )

    return vector_search


# ----------------------------------------------------------------
# Configuración semántica para el fields de razones
def create_semantic_config():
    semantic_config = SemanticConfiguration(
        name="semantic-config",
        prioritized_fields=SemanticPrioritizedFields(
            content_fields=[SemanticField(field_name="content_ltks")],
        ),
    )

    return semantic_config
