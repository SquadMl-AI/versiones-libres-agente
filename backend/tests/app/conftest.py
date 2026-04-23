
import importlib.util
import sys
import types
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SOURCE_DIR = BASE_DIR.parent.parent / "app"


def ensure_module(name: str):
    if name in sys.modules:
        return sys.modules[name]
    module = types.ModuleType(name)
    sys.modules[name] = module
    return module


def stub_module(name: str, **attrs):
    module = ensure_module(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    return module


class DummyRoute:
    def __init__(self, path):
        self.path = path

class DummyRouter:
    def __init__(self):
        self.routes = []
        self.included = []

    def post(self, path):
        def decorator(func):
            self.routes.append(DummyRoute(path))
            return func
        return decorator

    def get(self, path):
        def decorator(func):
            self.routes.append(DummyRoute(path))
            return func
        return decorator

    def put(self, path):
        def decorator(func):
            self.routes.append(DummyRoute(path))
            return func
        return decorator

    def include_router(self, router, prefix="", tags=None):
        self.included.append({"router": router, "prefix": prefix, "tags": tags or []})
        self.routes.append(DummyRoute(prefix))
        for route in getattr(router, 'routes', []):
            self.routes.append(DummyRoute(prefix + getattr(route, "path", "")))


class DummyHTTPException(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def dummy_query(default=None, **kwargs):
    return default


class DummyBaseModel:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def model_dump(self):
        return self.__dict__.copy()


class DummyFastAPI:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.routes = []
    def include_router(self, router, prefix="", *args, **kwargs):
        self.routes.append(DummyRoute(prefix))
        for route in getattr(router, 'routes', []):
            self.routes.append(DummyRoute(prefix + getattr(route, "path", "")))
    def add_middleware(self, *args, **kwargs):
        pass

class DummyAPIRouter(DummyRouter):
    pass


def setup_common_stubs():
    stub_module("dotenv", find_dotenv=lambda *a, **k: "", load_dotenv=lambda *a, **k: True)
    stub_module(
        "fastapi",
        APIRouter=DummyAPIRouter,
        HTTPException=DummyHTTPException,
        Query=dummy_query,
        FastAPI=DummyFastAPI,
    )
    stub_module("fastapi.middleware.cors", CORSMiddleware=object)
    stub_module("pydantic", BaseModel=DummyBaseModel)


class DummySearchCategoryChunks:
    def classification_pipeline_endpoint(self, query=None, collections=None, documents=None):
        return {"query": query, "collections": collections, "documents": documents}


class DummySynthesisCategoryChunks:
    def synthesis_pipeline_endpoint(self, query=None, chunks=None):
        return {"query": query, "chunks": chunks}


class DummyCosmos:
    def __init__(self, *args, **kwargs):
        self.inserted = []
        self.updated = []
        self.users = []
        self.messages = []

    def insert_message(self, data, collection_name=None, collection=None):
        self.inserted.append({"data": data, "collection_name": collection_name, "collection": collection})

    def update_message(self, filter_field, update_field, collection_name=None, collection=None):
        self.updated.append({"filter": filter_field, "update": update_field, "collection_name": collection_name, "collection": collection})

    def get_messages_by_user(self, user_email, collection_name):
        return self.messages

    def get_users_lists(self, collection_name=None, doc_ids=None):
        return self.users


class DummyBlobStorage:
    def __init__(self):
        self.calls = []
        self._list = []

    def list_blobs(self, prefix="", suffix="pdf"):
        self.calls.append((prefix, suffix))
        return self._list


class DummyAzureServices:
    AzureBlobStorage = DummyBlobStorage
    CosmosDB = DummyCosmos
    class AzureOpenAI:
        def __init__(self, *args, **kwargs):
            self.client_embeddings = object()
    class AzureIASearch:
        def __init__(self, *args, **kwargs):
            pass
    class DocumentIntelligence:
        def __init__(self, *args, **kwargs):
            pass


def setup_app_stubs():
    setup_common_stubs()
    ensure_module("app")
    ensure_module("app.services")
    ensure_module("app.utils")
    ensure_module("app.api")
    ensure_module("app.api.v1")
    ensure_module("app.api.v1")
    ensure_module("app.api.v1.endpoints")
    
    endpoints = ["advance_search", "blobs", "chat_ask", "feed_messages", "feedback_synthesis", "history_session", "synthesis", "users_auth"]
    for ep in endpoints:
        stub_module(f"app.api.v1.endpoints.{ep}", router=DummyAPIRouter())
        
    stub_module("app.api.v1.api", api_router=DummyAPIRouter())
    api_module = sys.modules["app.api.v1.api"]
    for route_str in ['/chat_ask', '/rag/sentencias', '/rag/audiencias', '/synthesis', '/advance_search', '/sessions', '/folders', '/files', '/users_auth', '/feedbacks', '/feed_message']:
        api_module.api_router.routes.append(DummyRoute(route_str))
        
    stub_module("app.services.search_category_service", SearchCategoryChunks=DummySearchCategoryChunks)
    stub_module("app.services.synthesis_service", SynthesisCategoryChunks=DummySynthesisCategoryChunks)
    stub_module("app.services.rag_service_audiencias", RAGPipelineAudiencias=type("R", (), {"rag_pipeline": lambda self, **kwargs: type("Resp", (), {"model":"m","answer":"a","sources":[],"model_dump":lambda self:{"model":"m","answer":"a","sources":[]}})() }))
    stub_module("app.services.rag_service_sentencias", RAGPipelineSentencias=type("R", (), {"rag_pipeline": lambda self, **kwargs: type("Resp", (), {"model":"m","answer":"a","sources":[],"model_dump":lambda self:{"model":"m","answer":"a","sources":[]}})() }))
    stub_module("app.utils.ai_services", AzureServices=DummyAzureServices)


def load_module_from_source(relative_path: str, module_name: str):
    path = SOURCE_DIR / relative_path
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module
