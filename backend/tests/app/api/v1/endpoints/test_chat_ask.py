from conftest import load_module_from_source, setup_app_stubs


def test_chat_ask_sentencias_persists_human_and_ai_messages():
    setup_app_stubs()
    module = load_module_from_source('api/v1/endpoints/chat_ask.py', 'src_endpoint_chat_ask')
    result = module.chat_ask_sentencias(module.RequestSentencias(query='consulta', user_email='user@test.com'))
    assert 'message_id' in result
    assert result['response']['answer'] == 'a'
    assert len(module.cosmos.inserted) == 2


def test_chat_ask_audiencias_persists_human_and_ai_messages():
    setup_app_stubs()
    module = load_module_from_source('api/v1/endpoints/chat_ask.py', 'src_endpoint_chat_ask_aud')
    result = module.chat_ask_audiencias(module.RequestAudiencias(query='consulta', user_email='user@test.com'))
    assert 'message_id' in result
    assert len(module.cosmos.inserted) == 2
