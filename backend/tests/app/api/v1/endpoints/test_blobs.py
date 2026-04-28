from conftest import load_module_from_source, setup_app_stubs


def test_get_folders_returns_unique_sorted_names():
    setup_app_stubs()
    module = load_module_from_source("api/v1/endpoints/blobs.py", "src_endpoint_blobs")
    module.blob._list = ["uno/a.pdf", "dos/b.pdf", "uno/c.pdf"]
    assert module.get_folders() == ["dos", "uno"]


def test_get_files_returns_file_names_for_selected_folders():
    setup_app_stubs()
    module = load_module_from_source("api/v1/endpoints/blobs.py", "src_endpoint_blobs_files")
    module.blob.list_blobs = lambda prefix="", suffix="pdf": {
        "uno/": ["uno/a.pdf", "uno/b.pdf"],
        "dos/": ["dos/c.pdf"],
    }.get(prefix, [])
    assert module.get_files(["uno", "dos"]) == ["a.pdf", "b.pdf", "c.pdf"]
