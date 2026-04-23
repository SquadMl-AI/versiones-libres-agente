import pytest

from conftest import DummyHTTPException, load_module_from_source, setup_app_stubs


def test_get_user_auth_returns_access_for_matching_email():
    setup_app_stubs()
    module = load_module_from_source('api/v1/endpoints/users_auth.py', 'src_endpoint_users_auth')
    module.cosmos.users = [{'CORREO': 'user@test.com', 'MODULO': 'sentencias'}, {'CORREO': 'USER@test.com', 'MODULO': 'audiencias'}]
    result = module.get_user_auth(module.UserAuth(e_mail='user@test.com'))
    assert result['correo'].lower() == 'user@test.com'
    assert sorted(result['access']) == ['audiencias', 'sentencias']


def test_get_user_auth_missing_user_is_wrapped_as_http_error():
    setup_app_stubs()
    module = load_module_from_source('api/v1/endpoints/users_auth.py', 'src_endpoint_users_auth_missing')
    module.cosmos.users = []
    with pytest.raises(DummyHTTPException) as exc:
        module.get_user_auth(module.UserAuth(e_mail='missing@test.com'))
    assert exc.value.status_code == 500
