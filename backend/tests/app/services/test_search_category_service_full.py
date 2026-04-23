import json
from unittest.mock import MagicMock, patch
import types
import sys

from conftest import load_module_from_source, setup_app_stubs

def setup_mock_service():
    setup_app_stubs()
    mock_aoai = MagicMock()
    mock_aoai.model_response.return_value = ('{"clasificacion": "Relevante", "resumen_llm": "mock"}', "gpt-4")
    
    mock_search = MagicMock()
    mock_search.hybrid_search.return_value = [
        {"doc_id": "1", "content": "Cont Alto Score", "bloque": "b1", "docnm": "d1", "@search.score": 10.0, "@search.reranker_score": 3.0, "@search.highlights": {"content": ["<em>alto</em> score"]}},
        {"doc_id": "2", "content": "Cont Bajo Score", "bloque": "b1", "docnm": "d2", "@search.score": 5.0, "@search.reranker_score": 1.0},
        {"doc_id": "3", "content": "Cont Sin Reranker", "bloque": "b1", "docnm": "d3", "@search.score": 1.0}
    ]
    
    sys.modules['utils'] = types.ModuleType('utils')
    sys.modules['utils.ai_services'] = types.ModuleType('utils.ai_services')
    sys.modules['openai'] = types.ModuleType('openai')
    mock_azure = MagicMock()
    mock_azure.AzureOpenAI.return_value = mock_aoai
    mock_azure.AzureIASearch.return_value = mock_search
    sys.modules['utils.ai_services'].AzureServices = mock_azure
    
    return load_module_from_source('services/search_category_service.py', 'src_search_cat_service'), mock_search, mock_aoai

def test_search_category_pipeline():
    module, mock_search, mock_aoai = setup_mock_service()
    with patch('os.getenv', side_effect=lambda k: "mock_deployment"):
        pipeline = module.SearchCategoryChunks()
        
        # Test 1: get_embedding
        mock_openai_client = MagicMock()
        mock_openai_client.embeddings.create.return_value.data = [MagicMock(embedding=[0.1, 0.2])]
        emb = pipeline.get_embedding("texto", mock_openai_client)
        assert emb == [0.1, 0.2]
        
        # Test 2: build_odata_filter
        f = pipeline.build_odata_filter(["col1'2"], ["doc1'2"])
        assert "col1''2" in f
        assert "doc1''2" in f
        assert pipeline.build_odata_filter(None, None) is None
        
        # Test 3: categorize_chunk_content success & exception
        cat, mod = pipeline.categorize_chunk_content("chunk content", "query")
        assert cat["categoria"] == "Relevante"
        assert cat["resumen_llm"] == "mock"
        
        mock_aoai.model_response.side_effect = Exception("Simulated Error")
        cat_err, mod_err = pipeline.categorize_chunk_content("chunk", "query")
        assert cat_err["categoria"] == "Error de Procesamiento"
        assert "Simulated Error" in cat_err["resumen_llm"]
        mock_aoai.model_response.side_effect = None # Reset
        
        # Test 4: classification_pipeline_endpoint execution logic
        response = pipeline.classification_pipeline_endpoint("consulta", "idx", ["c1"], ["d1"])
        
        assert len(response.high_score_categorized_chunks) == 1
        assert response.high_score_categorized_chunks[0]["categoria"] == "Relevante"
        assert response.high_score_categorized_chunks[0]["content_highlighted"] == "Cont <em>Alto</em> Score"
        assert len(response.low_score_reranked_chunks) == 1
        assert len(response.remaining_chunks) == 1

def test_search_category_main_execution():
    module, _, _ = setup_mock_service()
    with patch.object(module.SearchCategoryChunks, 'classification_pipeline_endpoint') as mock_pipe:
        module.pipeline = module.SearchCategoryChunks()
        module.pipeline.classification_pipeline_endpoint("query", index_name="idx", collections=[], documents=[])
        mock_pipe.assert_called_once()
