import sys
import types
from unittest.mock import MagicMock, patch

from conftest import load_module_from_source, setup_app_stubs


def test_rag_pipeline_audiencias():
    setup_app_stubs()

    mock_aoai = MagicMock()
    mock_aoai.model_response_with_history.return_value = ("Respuesta basada en [fuente 1] y [fuente 2]", "gpt-4")

    mock_search = MagicMock()
    mock_search.hybrid_search.return_value = [
        {"@search.reranker_score": 3, "content": "Contenido 1", "docnm": "doc1.pdf", "page_number": [1]},
        {"@search.reranker_score": 2.5, "content": "Contenido 2", "docnm": "doc2.pdf", "page_number": [2]},
    ]

    mock_cosmos = MagicMock()
    mock_cosmos.get_messages_by_user_and_time.return_value = [
        {"type": "human", "content": "Hola"},
        {"type": "ai", "content": '{"answer": "Hola respuesta"}'},
        {"type": "ai", "content": "string con literal dict"},
        {"type": "ai", "content": "bad json format"},
    ]

    # Mock global AzureServices for the module
    sys.modules["utils"] = types.ModuleType("utils")
    sys.modules["utils.ai_services"] = types.ModuleType("utils.ai_services")
    mock_azure = MagicMock()
    mock_azure.AzureOpenAI.return_value = mock_aoai
    mock_azure.AzureIASearch.return_value = mock_search
    mock_azure.CosmosDB.return_value = mock_cosmos
    sys.modules["utils.ai_services"].AzureServices = mock_azure

    with patch("os.getenv", side_effect=lambda k: "mock_value"):
        module = load_module_from_source("services/rag_service_audiencias.py", "src_rag_audiencias")
        pipeline = module.RAGPipelineAudiencias()

        response = pipeline.rag_pipeline("prueba de pregunta html <b>bold</b>", "test@test.com")

        assert response.model == "gpt-4"
        assert "Respuesta basada" in response.answer
        assert len(response.sources) == 2


def test_rag_pipeline_audiencias_no_chunks():
    setup_app_stubs()
    mock_azure = MagicMock()
    mock_azure.AzureOpenAI.return_value = MagicMock()
    mock_search = MagicMock()
    mock_search.hybrid_search.return_value = []
    mock_azure.AzureIASearch.return_value = mock_search
    mock_azure.CosmosDB.return_value = MagicMock()
    sys.modules["utils.ai_services"].AzureServices = mock_azure

    with patch("os.getenv", side_effect=lambda k: "mock_value"):
        module = load_module_from_source("services/rag_service_audiencias.py", "src_rag_audiencias2")
        pipeline = module.RAGPipelineAudiencias()
        response = pipeline.rag_pipeline("query", "test@test.com")
        assert len(response.sources) == 0
        assert "Lo siento" in response.answer


def test_rag_pipeline_audiencias_low_threshold_chunks():
    setup_app_stubs()
    mock_aoai = MagicMock()
    mock_aoai.model_response_with_history.return_value = ("Respuesta", "gpt-4")
    mock_search = MagicMock()
    # chunks below any threshold
    mock_search.hybrid_search.return_value = [{"@search.reranker_score": 0.5, "content": "Cont", "docnm": "doc"}]
    mock_azure = MagicMock()
    mock_azure.AzureOpenAI.return_value = mock_aoai
    mock_azure.AzureIASearch.return_value = mock_search
    mock_azure.CosmosDB.return_value = MagicMock()
    sys.modules["utils.ai_services"].AzureServices = mock_azure

    with patch("os.getenv", side_effect=lambda k: "mock_value"):
        module = load_module_from_source("services/rag_service_audiencias.py", "src_rag_audiencias3")
        pipeline = module.RAGPipelineAudiencias()
        response = pipeline.rag_pipeline("query", "test@test.com")
        assert len(response.sources) == 0
