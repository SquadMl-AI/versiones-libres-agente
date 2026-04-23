from conftest import load_module_from_source, setup_common_stubs


def test_search_models_expose_expected_fields():
    setup_common_stubs()
    module = load_module_from_source('schemas/search.py', 'src_schemas_search')
    item = module.SearchResult(id='1', title='T', content='C')
    assert item.id == '1'
    assert item.title == 'T'
    response = module.SearchResponse(results=[item], graph={'ok': True}, aggregations={'count': 1})
    assert response.results[0].title == 'T'
    request = module.SynthesisRequest(query='q', llm_model='gpt', results=[item])
    assert request.query == 'q'
    assert request.llm_model == 'gpt'


def test_feedback_request_accepts_expected_payload():
    setup_common_stubs()
    module = load_module_from_source('schemas/search.py', 'src_schemas_search_feedback')
    payload = module.FeedbackRequest(user_email='qa@test.com', query='consulta', rating=5, contar=1)
    assert payload.user_email == 'qa@test.com'
    assert payload.rating == 5
