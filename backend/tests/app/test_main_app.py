from conftest import load_module_from_source, setup_app_stubs


def test_main_app_initialization():
    setup_app_stubs()
    module = load_module_from_source('main.py', 'src_main_app')
    assert module.app is not None
    assert module.app.title == "Memorias de Justicia y Paz API"
    route_paths = [r.path for r in module.app.routes]
    assert any('/api/v1' in path for path in route_paths)
