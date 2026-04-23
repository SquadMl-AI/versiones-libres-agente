import asyncio

from conftest import load_module_from_source, setup_app_stubs


def test_advance_search_returns_service_response():
    setup_app_stubs()
    module = load_module_from_source('api/v1/endpoints/advance_search.py', 'src_endpoint_advance_search')
    request = module.Request(query='hola', bloque=['b1'], file=['f1.pdf'], user_id='u1')
    result = asyncio.run(module.advance_search(request))
    assert result['query'] == 'hola'
    assert result['collections'] == ['b1']
    assert result['documents'] == ['f1.pdf']
