import pytest

from conftest import DummyHTTPException, load_module_from_source, setup_app_stubs


def test_feed_message_updates_feed_value():
    setup_app_stubs()
    module = load_module_from_source("api/v1/endpoints/feed_messages.py", "src_endpoint_feed_messages")
    result = module.feed_message(module.MessagesFeedback(message_id="abc", feed=1))
    assert result["message"]
    assert module.cosmos.updated[0]["filter"] == {"_id": "abc"}
    assert module.cosmos.updated[0]["update"] == {"feed": 1}


def test_feed_message_raises_http_500_when_update_fails():
    setup_app_stubs()
    module = load_module_from_source("api/v1/endpoints/feed_messages.py", "src_endpoint_feed_messages_err")
    module.cosmos.update_message = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("db down"))
    with pytest.raises(DummyHTTPException) as exc:
        module.feed_message(module.MessagesFeedback(message_id="abc", feed=0))
    assert exc.value.status_code == 500
