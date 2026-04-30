import sys
import types
from unittest.mock import MagicMock, patch

from conftest import load_module_from_source, setup_app_stubs


def clear_rag_modules():
    modules_to_clear = [
        "services.rag_service_base",
        "services.rag_service_audiencias",
        "services.rag_service_sentencias",
    ]

    for module_name in modules_to_clear:
        sys.modules.pop(module_name, None)


def install_mock_azure_services(mock_aoai=None, mock_search=None, mock_cosmos=None):
    sys.modules["utils"] = types.ModuleType("utils")
    sys.modules["utils.ai_services"] = types.ModuleType("utils.ai_services")

    mock_azure = MagicMock()

    mock_azure.AzureOpenAI.return_value = mock_aoai or MagicMock()
    mock_azure.AzureIASearch.return_value = mock_search or MagicMock()
    mock_azure.CosmosDB.return_value = mock_cosmos or MagicMock()

    sys.modules["utils.ai_services"].AzureServices = mock_azure

    return mock_azure


def test_rag_pipeline_sentencias():
    clear_rag_modules()
    setup_app_stubs()

    mock_aoai = MagicMock()
    mock_aoai.model_response_with_history.return_value = (
        "Respuesta basada en [fuente 1] y [fuente 2]",
        "gpt-4",
    )

    mock_search = MagicMock()
    mock_search.hybrid_search.return_value = [
        {
            "@search.reranker_score": 3,
            "content": "Contenido 1",
            "docnm": "doc1.pdf",
            "page_number": [1],
        },
        {
            "@search.reranker_score": 2.5,
            "content": "Contenido 2",
            "docnm": "doc2.pdf",
            "page_number": [2],
        },
    ]

    mock_cosmos = MagicMock()
    mock_cosmos.get_messages_by_user_and_time.return_value = [
        {"type": "human", "content": "Hola"},
        {"type": "ai", "content": '{"answer": "Hola respuesta"}'},
    ]

    install_mock_azure_services(
        mock_aoai=mock_aoai,
        mock_search=mock_search,
        mock_cosmos=mock_cosmos,
    )

    with patch("os.getenv", side_effect=lambda key: "mock_value"):
        module = load_module_from_source(
            "services/rag_service_sentencias.py",
            "src_rag_sentencias",
        )

        pipeline = module.RAGPipelineSentencias()
        response = pipeline.rag_pipeline("prueba de pregunta", "test@test.com")

        assert response.model == "gpt-4"
        assert "Respuesta basada" in response.answer
        assert len(response.sources) == 2

        mock_search.hybrid_search.assert_called_once_with(
            "prueba de pregunta",
            "index_sentencias",
            50,
        )
        mock_cosmos.get_messages_by_user_and_time.assert_called_once()
        mock_aoai.model_response_with_history.assert_called_once()


def test_rag_pipeline_sentencias_no_chunks():
    clear_rag_modules()
    setup_app_stubs()

    mock_aoai = MagicMock()

    mock_search = MagicMock()
    mock_search.hybrid_search.return_value = []

    mock_cosmos = MagicMock()
    mock_cosmos.get_messages_by_user_and_time.return_value = []

    install_mock_azure_services(
        mock_aoai=mock_aoai,
        mock_search=mock_search,
        mock_cosmos=mock_cosmos,
    )

    with patch("os.getenv", side_effect=lambda key: "mock_value"):
        module = load_module_from_source(
            "services/rag_service_sentencias.py",
            "src_rag_sentencias_no_chunks",
        )

        pipeline = module.RAGPipelineSentencias()
        response = pipeline.rag_pipeline("query", "test@test.com")

        assert response.model is None
        assert len(response.sources) == 0
        assert "Lo siento" in response.answer

        mock_search.hybrid_search.assert_called_once_with(
            "query",
            "index_sentencias",
            50,
        )
        mock_aoai.model_response_with_history.assert_not_called()


def test_rag_pipeline_sentencias_main_execution():
    clear_rag_modules()
    setup_app_stubs()

    mock_aoai = MagicMock()
    mock_search = MagicMock()
    mock_cosmos = MagicMock()

    install_mock_azure_services(
        mock_aoai=mock_aoai,
        mock_search=mock_search,
        mock_cosmos=mock_cosmos,
    )

    with patch("os.getenv", side_effect=lambda key: "mock_value"):
        module = load_module_from_source(
            "services/rag_service_sentencias.py",
            "src_rag_sentencias_main",
        )

        with patch.object(module.RAGPipelineSentencias, "rag_pipeline") as mock_rag:
            module.ragpipeline = module.RAGPipelineSentencias()

            module.ragpipeline.rag_pipeline(
                "pregunta",
                index_name="index_sentencias",
                top_k=5,
                user_email="Default",
            )

            mock_rag.assert_called_once_with(
                "pregunta",
                index_name="index_sentencias",
                top_k=5,
                user_email="Default",
            )