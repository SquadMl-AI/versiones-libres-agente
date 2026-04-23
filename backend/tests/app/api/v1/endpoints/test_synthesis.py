import asyncio
from conftest import load_module_from_source, setup_app_stubs


def test_synthesis_endpoint_returns_service_payload():
    setup_app_stubs()
    module = load_module_from_source('api/v1/endpoints/synthesis.py', 'src_endpoint_synthesis')
    result = asyncio.run(module.advance_search(module.Request(query='q', chunks=[{'id': 1}])))
    assert result['query'] == 'q'
    assert result['chunks'] == [{'id': 1}]
