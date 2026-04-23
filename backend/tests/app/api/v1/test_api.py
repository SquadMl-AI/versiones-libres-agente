import sys
import types

from conftest import DummyRouter, load_module_from_source, setup_common_stubs


def test_api_router_includes_expected_endpoints():
    setup_common_stubs()
    sys.modules["app"] = types.ModuleType("app")
    sys.modules["app.api"] = types.ModuleType("app.api")
    sys.modules["app.api.v1"] = types.ModuleType("app.api.v1")
    endpoints = types.ModuleType("app.api.v1.endpoints")
    for name in [
        "advance_search",
        "blobs",
        "chat_ask",
        "feed_messages",
        "feedback_synthesis",
        "history_session",
        "synthesis",
        "users_auth",
    ]:
        mod = types.ModuleType(f"app.api.v1.endpoints.{name}")
        if name == "blobs":
            mod.router_folders = DummyRouter()
            mod.router_files = DummyRouter()
        elif name == "feedback_synthesis":
            mod.router_interaction = DummyRouter()
            mod.router_graph = DummyRouter()
            mod.router_synthe = DummyRouter()
            mod.router_stats_synthe = DummyRouter()
        else:
            mod.router = DummyRouter()
        sys.modules[f"app.api.v1.endpoints.{name}"] = mod
        setattr(endpoints, name, mod)
    sys.modules["app.api.v1.endpoints"] = endpoints
    module = load_module_from_source("api/v1/api.py", "src_api_v1_api")
    prefixes = [item["prefix"] for item in module.api_router.included]
    assert "/chat_ask" in prefixes
    assert "/synthesis_chuks" in prefixes
    assert "/advance_search" in prefixes
    assert "/sessions" in prefixes
    assert "/folders" in prefixes
    assert "/files" in prefixes
