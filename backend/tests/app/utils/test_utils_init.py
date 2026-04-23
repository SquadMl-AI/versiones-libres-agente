from conftest import load_module_from_source


def test_module_loads():
    module = load_module_from_source("utils/__init__.py", "mod_utils___init___py")
    assert module is not None
