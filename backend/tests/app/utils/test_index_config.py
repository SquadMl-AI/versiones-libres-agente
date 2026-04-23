import types
import sys
from conftest import load_module_from_source


class DummyField:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class DummySearchFieldDataType:
    String = 'String'
    Int32 = 'Int32'
    Single = 'Single'
    @staticmethod
    def Collection(inner):
        return f'Collection[{inner}]'


def test_index_config_builders_return_expected_shapes():
    sys.modules['azure'] = types.ModuleType('azure')
    sys.modules['azure.search'] = types.ModuleType('azure.search')
    sys.modules['azure.search.documents'] = types.ModuleType('azure.search.documents')
    sys.modules['azure.search.documents.indexes'] = types.ModuleType('azure.search.documents.indexes')
    sys.modules['azure.search.documents.indexes.models'] = types.ModuleType('azure.search.documents.indexes.models')
    models = sys.modules['azure.search.documents.indexes.models']
    models.HnswAlgorithmConfiguration = DummyField
    models.SearchField = DummyField
    models.SearchFieldDataType = DummySearchFieldDataType
    models.SemanticConfiguration = DummyField
    models.SemanticField = DummyField
    models.SemanticPrioritizedFields = DummyField
    models.SimpleField = DummyField
    models.VectorSearch = DummyField
    models.VectorSearchProfile = DummyField
    module = load_module_from_source('utils/index_config.py', 'src_utils_index_config')
    fields = module.create_fields()
    assert any(getattr(f, 'name', None) == 'doc_id' for f in fields)
    vector = module.create_vectorsearch()
    assert hasattr(vector, 'algorithms')
    semantic = module.create_semantic_config()
    assert getattr(semantic, 'name', None) == 'semantic-config'
