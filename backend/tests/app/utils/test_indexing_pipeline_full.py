import sys
import types
from unittest.mock import MagicMock, patch

from conftest import load_module_from_source, setup_app_stubs


def setup_mock_indexing():
    setup_app_stubs()
    sys.modules["utils"] = types.ModuleType("utils")
    sys.modules["utils.ai_services"] = types.ModuleType("utils.ai_services")
    sys.modules["utils.index_config"] = types.ModuleType("utils.index_config")

    sys.modules["utils.index_config"].create_fields = MagicMock(return_value=[])
    sys.modules["utils.index_config"].create_semantic_config = MagicMock(return_value={})
    sys.modules["utils.index_config"].create_vectorsearch = MagicMock(return_value={})

    mock_azure = MagicMock()
    mock_blob = MagicMock()
    mock_blob.download_file.return_value = b"pdf data"
    mock_azure.AzureBlobStorage.return_value = mock_blob

    mock_di = MagicMock()
    mock_poller = MagicMock()
    mock_res = MagicMock()
    mock_para = MagicMock(content="texto parrafo", role="")
    mock_para.bounding_regions = [MagicMock(page_number=1)]
    mock_res.paragraphs = [mock_para]
    mock_table = MagicMock()
    mock_table.bounding_regions = [MagicMock(page_number=1)]
    mock_res.tables = [mock_table]
    mock_poller.result.return_value = mock_res
    mock_di.extract_doc_text.return_value = ("", ["tabla"], "", mock_poller)
    mock_azure.DocumentIntelligence.return_value = mock_di

    mock_aoai = MagicMock()
    mock_aoai.client_embeddings = MagicMock()
    mock_aoai.embeddings_generation.return_value = [{"embedded_content_ltks": "val"}]
    mock_azure.AzureOpenAI.return_value = mock_aoai

    mock_search = MagicMock()
    mock_search.check_document_exists.return_value = False
    mock_search.consistent_encode.return_value = "encoded"
    mock_azure.AzureIASearch.return_value = mock_search

    sys.modules["utils.ai_services"].AzureServices = mock_azure

    # Mock PyMuPDF (fitz)
    sys.modules["fitz"] = types.ModuleType("fitz")
    mock_fitz_doc = MagicMock()
    mock_fitz_doc.page_count = 1
    sys.modules["fitz"].open = MagicMock(return_value=mock_fitz_doc)

    return (
        load_module_from_source("utils/indexing_pipeline.py", "src_indexing_pipe_full"),
        mock_search,
        mock_fitz_doc,
        mock_blob,
        mock_aoai,
    )


def test_reading_processing_documents():
    module, mock_search, _, mock_blob, _ = setup_mock_indexing()
    pipeline = module.DocumentProcessingPipeline()

    # Test document exists
    mock_search.check_document_exists.return_value = True
    d, t = pipeline.reading_processing_documents("Bloque/file.pdf", {}, "index")
    assert d is None and t is None

    # Test download fails
    mock_search.check_document_exists.return_value = False
    mock_blob.download_file.return_value = None
    d, t = pipeline.reading_processing_documents("Bloque/file.pdf", {}, "index")
    assert d is None and t is None

    # Test success flow
    mock_blob.download_file.return_value = b"pdf data"
    d, t = pipeline.reading_processing_documents("Bloque/file.pdf", {}, "index")
    assert len(d) == 1
    assert d[0]["content"] == "texto parrafo"
    assert len(t) == 1

    # Exception handling in check_document_exists
    mock_search.check_document_exists.side_effect = Exception("err")
    d, t = pipeline.reading_processing_documents("Bloque/file.pdf", {}, "index")
    assert len(d) == 1


def test_create_knowledge_base():
    module, mock_search, _, _, mock_aoai = setup_mock_indexing()
    pipeline = module.DocumentProcessingPipeline()

    r = pipeline.create_knowledge_base("index", [{"bloque": "b", "docnm": "d", "v": "1"}])
    mock_search.create_index.assert_called_once()
    mock_aoai.embeddings_generation.assert_called_once()
    mock_search.upload_documents.assert_called_once()
    assert len(r) == 1


def test_document_processing_indexing_orchestrator():
    module, _, _, mock_blob, _ = setup_mock_indexing()
    pipeline = module.DocumentProcessingPipeline()

    mock_blob.list_blobs.return_value = ["blob1", "blob2", "blob3", "Bloque/file.pdf"]

    with patch.object(pipeline, "reading_processing_documents", return_value=([], [])):
        # Skipping logic for empty reading
        res = pipeline.document_processing_indexing_orchestrator({}, "index")

    with (
        patch.object(
            pipeline,
            "reading_processing_documents",
            return_value=(
                [{"content": "c", "docnm_kwd": "d", "docnm": "d", "bloque": "b", "kb_id": "1", "page_number": 1}],
                [],
            ),
        ),
        patch.object(pipeline, "semantic_chunking", return_value=[{"content": "chunk", "docnm_kwd": "d"}]),
        patch.object(pipeline, "normalize_data", return_value=[{"content": "chunk"}]),
        patch.object(pipeline, "create_knowledge_base", return_value=[{"e": 1}]),
    ):
        res = pipeline.document_processing_indexing_orchestrator({}, "index")
        assert len(res) == 1


def test_indexing_pipeline_main():
    module, _, _, _, _ = setup_mock_indexing()
    with (
        patch("builtins.open", MagicMock()),
        patch("json.load", return_value={}),
        patch("json.dump", MagicMock()),
        patch.object(module.DocumentProcessingPipeline, "document_processing_indexing_orchestrator") as mock_orch,
    ):
        module.pipeline = module.DocumentProcessingPipeline()
        # Cannot test literally the __main__ script easily, but we can call what is inside it.
        module.pipeline.document_processing_indexing_orchestrator({})
        mock_orch.assert_called_once()
