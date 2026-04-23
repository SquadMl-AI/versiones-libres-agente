import json
from unittest.mock import MagicMock, patch

from conftest import load_module_from_source, setup_app_stubs

def test_indexing_service_execution():
    setup_app_stubs()
    mock_pipeline = MagicMock()
    mock_pipeline.document_processing_indexing_orchestrator.return_value = {"status": "ok"}
    
    mock_file = MagicMock()
    mock_file.__enter__.return_value.read.return_value = '{"id": "test"}'
    
    import sys
    import types
    sys.modules['utils'] = types.ModuleType('utils')
    sys.modules['utils.indexing_pipeline'] = types.ModuleType('utils.indexing_pipeline')
    sys.modules['utils.indexing_pipeline'].DocumentProcessingPipeline = MagicMock(return_value=mock_pipeline)
    
    with patch('pathlib.Path.open', return_value=MagicMock(__enter__=MagicMock(return_value=MagicMock(read=lambda: '{"id": "test"}', write=MagicMock())))):
        with patch('json.load', return_value={"id": "test"}):
            with patch('json.dump') as mock_dump:
                module = load_module_from_source('services/indexing_service.py', 'src_services_indexing_service')
                
                mock_pipeline.document_processing_indexing_orchestrator.assert_called_once()
                mock_dump.assert_called_once()
