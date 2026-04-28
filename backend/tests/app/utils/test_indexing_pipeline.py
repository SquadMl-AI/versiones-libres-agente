import sys
import types

from conftest import load_module_from_source


class DummyDocument:
    def __init__(self, page_content):
        self.page_content = page_content


class DummyChunker:
    def split_documents(self, docs):
        content = docs[0].page_content
        return [DummyDocument(page_content=content.split(". ")[0])]


def prepare_module():
    sys.modules["fitz"] = types.ModuleType("fitz")
    sys.modules["bs4"] = types.ModuleType("bs4")
    sys.modules["bs4"].BeautifulSoup = lambda text, parser: type(
        "Soup", (), {"get_text": lambda self, separator=" ": text.replace("<p>", "").replace("</p>", "")}
    )()
    sys.modules["dotenv"] = types.ModuleType("dotenv")
    sys.modules["dotenv"].find_dotenv = lambda *a, **k: ""
    sys.modules["dotenv"].load_dotenv = lambda *a, **k: True
    sys.modules["langchain"] = types.ModuleType("langchain")
    sys.modules["langchain.docstore"] = types.ModuleType("langchain.docstore")
    sys.modules["langchain.docstore.document"] = types.ModuleType("langchain.docstore.document")
    sys.modules["langchain.docstore.document"].Document = DummyDocument
    sys.modules["langchain_experimental"] = types.ModuleType("langchain_experimental")
    sys.modules["langchain_experimental.text_splitter"] = types.ModuleType("langchain_experimental.text_splitter")
    sys.modules["langchain_experimental.text_splitter"].SemanticChunker = lambda *a, **k: DummyChunker()
    sys.modules["utils"] = types.ModuleType("utils")
    sys.modules["utils.ai_services"] = types.ModuleType("utils.ai_services")
    sys.modules["utils.ai_services"].AzureServices = type(
        "AzureServices",
        (),
        {
            "AzureBlobStorage": type("B", (), {}),
            "DocumentIntelligence": type("D", (), {}),
            "AzureOpenAI": type("O", (), {"__init__": lambda self: setattr(self, "client_embeddings", object())}),
            "AzureIASearch": type("S", (), {}),
        },
    )
    sys.modules["utils.index_config"] = types.ModuleType("utils.index_config")
    sys.modules["utils.index_config"].create_fields = lambda: ["f"]
    sys.modules["utils.index_config"].create_semantic_config = lambda: "semantic"
    sys.modules["utils.index_config"].create_vectorsearch = lambda: "vector"
    return load_module_from_source("utils/indexing_pipeline.py", "src_utils_indexing_pipeline")


def test_normalize_data_generates_search_fields():
    module = prepare_module()
    pipeline = module.DocumentProcessingPipeline.__new__(module.DocumentProcessingPipeline)
    data = [{"content": "<p>Árbol y acción.</p>", "docnm_kwd": "Mi Documento.PDF"}]
    result = module.DocumentProcessingPipeline.normalize_data(pipeline, data)
    assert result[0]["content_ltks"] == "arbol y accion"
    assert result[0]["docnm_tks"] == "mi documento.pdf"


def test_semantic_chunking_returns_chunks_with_metadata():
    module = prepare_module()
    pipeline = module.DocumentProcessingPipeline.__new__(module.DocumentProcessingPipeline)
    pipeline.chunker = DummyChunker()
    json_data = [
        {
            "docnm_kwd": "doc",
            "docnm": "doc.pdf",
            "bloque": "b1",
            "kb_id": "kb1",
            "content": "Primera parte. Segunda parte.",
            "page_number": 1,
        }
    ]
    result = module.DocumentProcessingPipeline.semantic_chunking(pipeline, json_data, [])
    assert result[0]["docnm"] == "doc.pdf"
    assert "content" in result[0]
