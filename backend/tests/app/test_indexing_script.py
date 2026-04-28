import sys
import types
from unittest.mock import MagicMock, patch

from conftest import load_module_from_source, setup_app_stubs


def test_indexing_main_execution():
    setup_app_stubs()

    # Extra mocks for indexing script
    sys.modules["langchain_experimental"] = types.ModuleType("langchain_experimental")
    sys.modules["langchain_experimental.text_splitter"] = types.ModuleType("langchain_experimental.text_splitter")

    mock_chunker = MagicMock()
    mock_chunker.split_text.return_value = ["chunk1", "chunk2"]
    sys.modules["langchain_experimental.text_splitter"].SemanticChunker = MagicMock(return_value=mock_chunker)

    # Mock services
    sys.modules["services"] = types.ModuleType("services")
    sys.modules["services.ai_services"] = types.ModuleType("services.ai_services")

    mock_azure = MagicMock()
    mock_blob = MagicMock()
    mock_blob.download_file.return_value = b"pdf data"
    mock_azure.AzureBlobStorage.return_value = mock_blob

    mock_di = MagicMock()
    mock_di.extract_doc_text.return_value = ("Extracted Text", [], 1, None)
    mock_azure.DocumentIntelligence.return_value = mock_di

    mock_openai = MagicMock()
    mock_openai.client_embeddings = "simulated_embeddings"
    mock_azure.AzureOpenAI.return_value = mock_openai

    sys.modules["services.ai_services"].AzureServices = mock_azure

    module = load_module_from_source("indexing.py", "src_indexing")

    with patch.object(module, "pdb"):
        module.main()

    mock_blob.download_file.assert_called_once()
    mock_di.extract_doc_text.assert_called_once()
    mock_chunker.split_text.assert_called_once_with("Extracted Text")


def test_indexing_main_download_fails():
    setup_app_stubs()
    sys.modules["langchain_experimental.text_splitter"] = types.ModuleType("langchain_experimental.text_splitter")
    sys.modules["langchain_experimental.text_splitter"].SemanticChunker = MagicMock()

    mock_azure = MagicMock()
    mock_blob = MagicMock()
    mock_blob.download_file.return_value = None
    mock_azure.AzureBlobStorage.return_value = mock_blob
    sys.modules["services"] = types.ModuleType("services")
    sys.modules["services.ai_services"] = types.ModuleType("services.ai_services")
    sys.modules["services.ai_services"].AzureServices = mock_azure

    module = load_module_from_source("indexing.py", "src_indexing_fail")
    module.main()
    mock_blob.download_file.assert_called_once()
