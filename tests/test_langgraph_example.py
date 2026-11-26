"""The LangGraph example's nodes (run in order when langgraph is not installed): 1 model call for the whole task."""
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("lg", os.path.join(HERE, "..", "examples", "langgraph_state.py"))
lg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lg)


def test_one_call_and_synced_copies(monkeypatch):
    monkeypatch.delenv("RSOS_MODEL", raising=False)
    start = {"auth.timeout_ms": "700", "auth.retries": "3", "auth.region": "eu", "search.retries": "6",
             "search.region": "us"}
    out = lg.run({"state": start, "requests": ["a", "b", "c"],
                  "copies": {"worker": {**start, "auth.retries": "2"}, "checker": dict(start)}})
    assert out["model_calls"] == 1
    assert out["state"] == {**start, "auth.timeout_ms": "800", "auth.retries": "8", "search.region": "eu"}
    assert out["report"]["failed"] == []
    assert out["copies"]["worker"] == out["copies"]["checker"] == out["state"]
