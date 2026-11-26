from rsoslang.painting.graphs import read_graph, patch

G = {"nodes": [{"id": "__start__"}, {"id": "router"}, {"id": "retrieve_docs"}, {"id": "agent_llm"},
               {"id": "search_tool"}, {"id": "critic"}, {"id": "__end__"}],
     "edges": [{"source": "__start__", "target": "router"}, {"source": "router", "target": "retrieve_docs", "conditional": True},
               {"source": "router", "target": "agent_llm", "conditional": True}, {"source": "retrieve_docs", "target": "agent_llm"},
               {"source": "agent_llm", "target": "search_tool"}, {"source": "search_tool", "target": "agent_llm"},
               {"source": "agent_llm", "target": "critic"}, {"source": "critic", "target": "__end__"}]}


def test_graph_is_painted_with_roles():
    s = read_graph(G)
    kinds = {o["name"]: o["kind"] for o in s["objects"]}
    assert kinds == {"__start__": "door", "router": "sky", "retrieve_docs": "lake", "agent_llm": "bird",
                     "search_tool": "engine", "critic": "owl", "__end__": "bridge"}
    assert any(l["conditional"] for l in s["links"])


def test_gestures_become_graph_edits():
    s = read_graph(G)
    e = patch(s, [("pierce", "guardrail", "agent_llm", "head"), ("grey", None, "search_tool", None),
                  ("near", "logger", "critic", None)])
    assert e[0] == {"edit": "insert_before", "node": "agent_llm", "new": "guardrail"}
    assert e[1]["edit"] == "sandbox" and e[2]["affects"] == "successors only"
