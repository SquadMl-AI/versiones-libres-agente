from conftest import load_module_from_source


def test_module_loads():
    module = load_module_from_source("api/v1/__init__.py", "mod_api_v1___init___py")
    assert module is not None
