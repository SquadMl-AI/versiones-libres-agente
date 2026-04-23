import sys
import types
from conftest import load_module_from_source


def prepare_module():
    sys.modules['fitz'] = types.ModuleType('fitz')
    sys.modules['fitz'].open = lambda *a, **k: (_ for _ in ()).throw(RuntimeError('bad pdf'))
    sys.modules['numpy'] = types.ModuleType('numpy')
    sys.modules['numpy'].max = max
    sys.modules['numpy'].zeros = lambda shape, dtype=str: [["" for _ in range(shape[1])] for _ in range(shape[0])]
    sys.modules['openai'] = types.ModuleType('openai')
    sys.modules['pandas'] = types.ModuleType('pandas')
    sys.modules['pandas'].DataFrame = lambda data, dtype=str: data
    for name in ['azure', 'azure.ai', 'azure.ai.formrecognizer', 'azure.core', 'azure.core.credentials', 'azure.core.exceptions', 'azure.search', 'azure.search.documents', 'azure.search.documents.indexes', 'azure.search.documents.indexes.models', 'azure.search.documents.models', 'azure.storage', 'azure.storage.blob', 'langchain_openai', 'pymongo', 'pymongo.errors', 'dotenv']:
        sys.modules[name] = types.ModuleType(name)
    sys.modules['azure.ai.formrecognizer'].DocumentAnalysisClient = type('DocumentAnalysisClient', (), {'__init__': lambda self, *a, **k: None})
    sys.modules['azure.core.credentials'].AzureKeyCredential = lambda key: key
    class ResourceNotFoundError(Exception):
        pass
    sys.modules['azure.core.exceptions'].ResourceNotFoundError = ResourceNotFoundError
    sys.modules['azure.search.documents'].SearchClient = object
    sys.modules['azure.search.documents.indexes'].SearchIndexClient = object
    sys.modules['azure.search.documents.indexes.models'].SearchField = object
    sys.modules['azure.search.documents.indexes.models'].SearchIndex = object
    sys.modules['azure.search.documents.indexes.models'].SemanticSearch = object
    sys.modules['azure.search.documents.models'].QueryType = object
    sys.modules['azure.search.documents.models'].VectorizedQuery = object
    class BlobServiceClient:
        @staticmethod
        def from_connection_string(conn):
            return type('Svc', (), {'get_container_client': lambda self, name: type('Container', (), {'list_blobs': lambda self, name_starts_with='': [type('B', (), {'name':'a/file1.pdf'})(), type('B', (), {'name':'a/file2.txt'})()]})()})()
    sys.modules['azure.storage.blob'].BlobServiceClient = BlobServiceClient
    sys.modules['dotenv'].find_dotenv = lambda *a, **k: ''
    sys.modules['dotenv'].load_dotenv = lambda *a, **k: True
    sys.modules['langchain_openai'].AzureChatOpenAI = object
    sys.modules['langchain_openai'].AzureOpenAIEmbeddings = object
    sys.modules['pymongo'].MongoClient = object
    sys.modules['pymongo.errors'].ServerSelectionTimeoutError = RuntimeError
    return load_module_from_source('utils/ai_services.py', 'src_utils_ai_services')


def test_blob_storage_list_blobs_filters_by_suffix():
    module = prepare_module()
    storage = module.AzureServices.AzureBlobStorage()
    storage.connection_string = 'UseDevelopmentStorage=true'
    storage.container_name = 'test'
    result = storage.list_blobs(prefix='a/', suffix='pdf')
    assert result == ['a/file1.pdf']


def test_blob_storage_page_count_error_returns_inf():
    module = prepare_module()
    storage = module.AzureServices.AzureBlobStorage()
    assert storage.get_pdf_page_count(b'broken') == float('inf')
