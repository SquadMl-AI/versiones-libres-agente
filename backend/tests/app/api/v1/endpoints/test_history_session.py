import pytest

from conftest import DummyHTTPException, load_module_from_source, setup_app_stubs


def test_get_history_returns_messages_from_cosmos():
    setup_app_stubs()
    module = load_module_from_source('api/v1/endpoints/history_session.py', 'src_endpoint_history_session')
    module.cosmos.messages = [{'content': 'hola'}]
    assert module.get_history('user@test.com') == [{'content': 'hola'}]


def test_get_history_wraps_errors_as_http_500():
    setup_app_stubs()
    module = load_module_from_source('api/v1/endpoints/history_session.py', 'src_endpoint_history_session_err')
    module.cosmos.get_messages_by_user = lambda *a, **k: (_ for _ in ()).throw(RuntimeError('db'))
    with pytest.raises(DummyHTTPException) as exc:
        module.get_history('user@test.com')
    assert exc.value.status_code == 500
