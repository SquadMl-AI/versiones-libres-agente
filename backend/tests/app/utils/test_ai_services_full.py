from unittest.mock import MagicMock, patch
from conftest import load_module_from_source, setup_app_stubs
import types
import sys

def test_azure_services_full():
    sys.modules.pop('numpy', None)
    sys.modules.pop('pandas', None)
    setup_app_stubs()
    
    # Needs to mock Azure modules
    sys.modules['azure.storage.blob'] = types.ModuleType('azure.storage.blob')
    sys.modules['azure.storage.blob'].BlobServiceClient = MagicMock()
    sys.modules['azure.storage.blob'].generate_blob_sas = MagicMock()
    sys.modules['azure.storage.blob'].BlobSasPermissions = MagicMock()
    
    sys.modules['azure.cosmos'] = types.ModuleType('azure.cosmos')
    sys.modules['azure.cosmos'].CosmosClient = MagicMock()
    sys.modules['azure.cosmos.exceptions'] = types.ModuleType('azure.cosmos.exceptions')
    sys.modules['azure.cosmos.exceptions'].CosmosResourceNotFoundError = Exception
    
    sys.modules['azure.search.documents'] = types.ModuleType('azure.search.documents')
    sys.modules['azure.search.documents'].SearchClient = MagicMock()
    sys.modules['azure.search.documents.indexes'] = types.ModuleType('azure.search.documents.indexes')
    sys.modules['azure.search.documents.indexes'].SearchIndexClient = MagicMock
    sys.modules['azure.search.documents.indexes.models'] = types.ModuleType('azure.search.documents.indexes.models')
    sys.modules['azure.search.documents.indexes.models'].SearchField = MagicMock
    sys.modules['azure.search.documents.indexes.models'].SearchIndex = MagicMock
    sys.modules['azure.search.documents.indexes.models'].SemanticSearch = MagicMock
    sys.modules['azure.search.documents.models'] = types.ModuleType('azure.search.documents.models')
    sys.modules['azure.search.documents.models'].VectorizedQuery = MagicMock
    sys.modules['azure.search.documents.models'].QueryType = MagicMock()
    
    sys.modules['azure.ai.documentintelligence'] = types.ModuleType('azure.ai.documentintelligence')
    sys.modules['azure.ai.documentintelligence'].DocumentIntelligenceClient = MagicMock()
    sys.modules['azure.ai.documentintelligence.models'] = types.ModuleType('azure.ai.documentintelligence.models')
    sys.modules['azure.ai.documentintelligence.models'].AnalyzeDocumentRequest = MagicMock
    
    sys.modules['azure.ai.formrecognizer'] = types.ModuleType('azure.ai.formrecognizer')
    sys.modules['azure.ai.formrecognizer'].DocumentAnalysisClient = MagicMock
    
    sys.modules['azure.core.credentials'] = types.ModuleType('azure.core.credentials')
    sys.modules['azure.core.credentials'].AzureKeyCredential = MagicMock
    
    sys.modules['openai'] = types.ModuleType('openai')
    sys.modules['openai'].AzureOpenAI = MagicMock()
    
    sys.modules['langchain_openai'] = types.ModuleType('langchain_openai')
    sys.modules['langchain_openai'].AzureChatOpenAI = MagicMock
    sys.modules['langchain_openai'].AzureOpenAIEmbeddings = MagicMock
    
    sys.modules['pymongo'] = types.ModuleType('pymongo')
    sys.modules['pymongo.errors'] = types.ModuleType('pymongo.errors')
    sys.modules['pymongo'].MongoClient = MagicMock(return_value=MagicMock())
    sys.modules['pymongo.errors'].ServerSelectionTimeoutError = Exception
    
    sys.modules['fitz'] = types.ModuleType('fitz')
    mock_pdf = MagicMock()
    mock_pdf.page_count = 1
    mock_pdf.tobytes.return_value = b'data'
    sys.modules['fitz'].open = MagicMock(return_value=mock_pdf)
    
    with patch('os.getenv', side_effect=lambda k: "fake"):
        module = load_module_from_source('utils/ai_services.py', 'src_ai_services_full')
        
        # 1. BlobStorage
        blob_storage = module.AzureServices.AzureBlobStorage()
        blob_storage._get_blob_service_client = MagicMock()
        blob_storage._get_blob_service_client().get_container_client.return_value.get_blob_client.return_value.download_blob.return_value.readall.return_value = b'data'
        assert blob_storage.download_file("file") == b'data'
        
        blob_storage._get_blob_properties = MagicMock(return_value={"size": 100})
        blob_storage._get_blob_service_client = MagicMock(side_effect=Exception("err"))
        assert blob_storage.download_file("f") is None
        
        # 2. DocumentIntelligence
        di = module.AzureServices.DocumentIntelligence()
        mock_poller = MagicMock()
        mock_poller.result.return_value.content = "text"
        
        mock_cell = MagicMock()
        mock_cell.row_index = 0
        mock_cell.column_index = 0
        mock_cell.content = "cell_text"
        mock_table = MagicMock()
        mock_table.cells = [mock_cell]
        mock_poller.result.return_value.tables = [mock_table]
        
        mock_line = MagicMock()
        mock_line.content = "text"
        mock_page = MagicMock()
        mock_page.lines = [mock_line]
        mock_poller.result.return_value.pages = [mock_page]
        
        di.document_analysis_client.begin_analyze_document.return_value = mock_poller
        
        txt, tabs, pages, pl_res = di.extract_doc_text(file_obj=b'data')
        assert txt == "Page 1:\ntext"
        
        mock_err_poller = MagicMock()
        mock_err_poller.result.side_effect = Exception("err")
        di.document_analysis_client.begin_analyze_document.return_value = mock_err_poller
        di.extract_doc_text(file_obj=b'data')
        
        # 3. AzureOpenAI
        aoai = module.AzureServices.AzureOpenAI()
        aoai.openai_client.chat.completions.create.return_value.choices = [MagicMock()]
        aoai.openai_client.chat.completions.create.return_value.choices[0].message.content = "response"
        aoai.openai_client.chat.completions.create.return_value.model = "gpt"
        resp, mod = aoai.model_response("u", "s", {"type": "json_object"})
        assert resp == "response"
        
        resp_hist, mod_hist = aoai.model_response_with_history("u", "s", [])
        assert resp_hist == "response"
        
        aoai.openai_client.embeddings.create.return_value.data = [MagicMock(embedding=[0.1])]
        emb = aoai.get_embedding("t")
        assert emb == [0.1]
        
        aoai.openai_client.chat.completions.create.side_effect = Exception("err")
        try:
            aoai.model_response("u", "s")
        except Exception:
            pass
            
        try:
            aoai.model_response_with_history("u", "s", [])
        except Exception:
            pass
        
        aoai.openai_client.embeddings.create.side_effect = Exception("err")
        try:
            aoai.get_embedding("t")
        except Exception:
            pass
        
        # 4. CosmosDB
        cosmos = module.AzureServices.CosmosDB("fake_conn", "fake_db", ["fake_col"])
        
        mock_col = MagicMock()
        cosmos.db = MagicMock()
        cosmos.db.__getitem__.return_value = mock_col
        
        mock_result = MagicMock()
        mock_result.inserted_id = "1"
        mock_col.insert_one.return_value = mock_result
        cosmos.insert_message({"id": 1}, "Graphs_Users")
        
        # Simulating exceptions in Cosmos
        mock_col.insert_one.side_effect = Exception("err")
        cosmos.insert_message({}, "Graphs_Users")
        
        mock_col.find.return_value = [{"_id": 1, "item": 1}]
        r = cosmos.get_messages_by_user_and_time("test", "Graphs_Users")
        assert len(r) == 1
        
        mock_col.find.side_effect = Exception("err")
        assert cosmos.get_messages_by_user_and_time("test", "Graphs_Users") == []
        
        mock_col.update_one.return_value.modified_count = 1
        cosmos.update_users_field({"_id": 1, "users": []}, "Graphs_Users")
        
        # 5. AzureIASearch
        search = module.AzureServices.AzureIASearch()
        
        sys.modules['azure.search.documents'].SearchClient.return_value.search.return_value = [{"@search.score": 1, "content": "c"}]
        
        with patch.object(module.AzureServices.AzureOpenAI, 'get_embedding', return_value=[0.1]*1536):
            res = search.hybrid_search("q", "idx")
            assert len(res) == 1
        
        sys.modules['azure.search.documents'].SearchClient.return_value.search.side_effect = Exception("err")
        with patch.object(module.AzureServices.AzureOpenAI, 'get_embedding', return_value=[0.1]*1536):
            try:
                search.hybrid_search("q", "idx")
            except Exception:
                pass
