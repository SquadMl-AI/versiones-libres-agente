# backend/tests/test_smoke.py
"""
Smoke tests: verifican que los módulos principales del backend se pueden
importar sin errores de dependencia o de configuración.

Estos tests requieren que las dependencias completas del proyecto estén
instaladas (requirements.txt). En CI se ejecutan en el job 'test'.
"""


def test_app_creates():
    from conftest import load_module_from_source, setup_app_stubs

    setup_app_stubs()
    m = load_module_from_source("main.py", "src_main_smoke")
    assert m.app is not None
    assert m.app.title == "Memorias de Justicia y Paz API"


def test_api_router_has_routes():
    from conftest import load_module_from_source, setup_app_stubs

    setup_app_stubs()
    m = load_module_from_source("api/v1/api.py", "src_api_smoke")
    assert len(m.api_router.routes) > 0


def test_expected_prefixes_registered():
    from conftest import load_module_from_source, setup_app_stubs

    setup_app_stubs()
    m = load_module_from_source("main.py", "src_main_smoke_2")
    route_paths = [r.path for r in m.app.routes]
    expected_fragments = [
        "/chat_ask",
        "/synthesis",
        "/advance_search",
        "/sessions",
        "/folders",
        "/files",
        "/users_auth",
        "/feedbacks",
        "/feed_message",
    ]
    for fragment in expected_fragments:
        assert any(fragment in path for path in route_paths)
