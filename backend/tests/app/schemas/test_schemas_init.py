from conftest import load_module_from_source


def test_module_loads():
    module = load_module_from_source("schemas/__init__.py", "mod_schemas___init___py")
    assert module is not None
