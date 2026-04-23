import sys
import types
from unittest.mock import MagicMock, patch

from conftest import load_module_from_source, setup_app_stubs


def setup_mock_synthesis():
    setup_app_stubs()
    mock_aoai = MagicMock()
    mock_aoai.model_response.return_value = ("Texto sintetizado mockeado", "gpt-4")

    sys.modules['utils'] = types.ModuleType('utils')
    sys.modules['utils.ai_services'] = types.ModuleType('utils.ai_services')
    mock_azure = MagicMock()
    mock_azure.AzureOpenAI.return_value = mock_aoai
    mock_azure.AzureIASearch.return_value = MagicMock()
    sys.modules['utils.ai_services'].AzureServices = mock_azure

    return load_module_from_source('services/synthesis_service.py', 'src_synthesis_service'), mock_aoai

def test_synthesis_service_pipeline():
    module, mock_aoai = setup_mock_synthesis()

    pipeline = module.SynthesisCategoryChunks()

    chunks = [
        {"document_name": "Sentencia-1999.pdf", "folder": "Autor A", "page_numbers": [1], "content": "c1"},
        {"document_name": "Libro-1999.pdf", "folder": "Autor A", "page_numbers": [2], "content": "c2"},
        {"document_name": "Unknown.pdf", "folder": "Autor B", "page_numbers": [3], "content": "c3"},
        {"document_name": "Sin-Anio.pdf", "folder": "Autor C", "page_numbers": [4], "content": "c4"}
    ]

    response = pipeline.synthesis_pipeline_endpoint("query", chunks)

    assert response.model == "gpt-4"
    assert response.synthesized_text == "Texto sintetizado mockeado"

    # Test error fallback in synthesis exception
    mock_aoai.model_response.side_effect = Exception("error")
    resp_err = pipeline.synthesis_pipeline_endpoint("query", chunks)
    assert resp_err is None

def test_synthesis_service_main_execution():
    module, _ = setup_mock_synthesis()
    with patch.object(module.SynthesisCategoryChunks, 'synthesis_pipeline_endpoint') as mock_endpoint:
        module.synthesis_category_chunks = module.SynthesisCategoryChunks()
        module.synthesis_category_chunks.synthesis_pipeline_endpoint("query", [])
        mock_endpoint.assert_called_once()
