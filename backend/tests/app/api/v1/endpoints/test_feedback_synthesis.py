from conftest import load_module_from_source, setup_app_stubs


def test_feed_back_inserts_feedback_document():
    setup_app_stubs()
    module = load_module_from_source("api/v1/endpoints/feedback_synthesis.py", "src_endpoint_feedback_synthesis")
    req = module.Request(
        user_email="u@test.com",
        query="q",
        model="gpt",
        results=[],
        stars_graph=5,
        feed_graph="ok",
        stars_synthe=4,
        feed_synthe="bien",
        synthesis="texto",
    )
    result = module.feed_back(req)
    assert result["message"] == "Feedback guardado con éxito"
    assert len(module.cosmos.inserted) == 1


def test_update_graph_feedback_updates_expected_fields():
    setup_app_stubs()
    module = load_module_from_source("api/v1/endpoints/feedback_synthesis.py", "src_endpoint_feedback_synthesis_graph")
    result = module.update_graph_feedback(module.UpdateGraphRequest(feedback_id="f1", stars_graph=3, feed_graph="ok"))
    assert "actualizados" in result["message"]
    assert module.cosmos.updated[0]["update"]["stars_graph"] == 3


def test_update_synthe_content_and_stats():
    setup_app_stubs()
    module = load_module_from_source("api/v1/endpoints/feedback_synthesis.py", "src_endpoint_feedback_synthesis_synth")
    result_1 = module.update_synthe_content(module.UpdateSyntheRequest(feedback_id="f1", synthesis="nuevo"))
    result_2 = module.update_synthe_stats(
        module.UpdateStatsSyntheRequest(feedback_id="f1", stars_synthe=4, feed_synthe="bien")
    )
    assert "actualizado" in result_1["message"]
    assert "actualizados" in result_2["message"]
