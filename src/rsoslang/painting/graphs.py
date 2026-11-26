"""Paint an external agent graph automatically (T6): a LangGraph-style JSON export → scene → gestures → patch.

Input format (as produced by a LangGraph graph's JSON export): {"nodes": [{"id": ..., "data": {...}}],
"edges": [{"source": ..., "target": ..., "conditional": bool}]}. LangGraph is not installed in this environment, so the
reader is built from this documented shape and tested on example graphs; gestures produce a patch (the graph edits to
make), not an executed run.
"""

ROLE_WORDS = [("policy", ["guard", "policy", "approve", "safety", "supervisor", "router"]),
              ("memory", ["memory", "retriev", "rag", "store", "cache", "kb"]),
              ("tool", ["tool", "search", "api", "call", "action", "execute"]),
              ("check", ["check", "verify", "valid", "eval", "critic", "review"]),
              ("reason", ["plan", "agent", "llm", "reason", "think", "classif", "decide"]),
              ("input", ["__start__", "input", "intake", "parse"]),
              ("output", ["__end__", "output", "respond", "answer", "final"])]
LAYER = {"policy": 0, "reason": 1, "check": 1, "memory": 2, "tool": 2, "transform": 2, "input": 3, "output": 3}
KIND = {"input": "door", "transform": "path", "reason": "bird", "memory": "lake", "policy": "sky", "tool": "engine",
        "check": "owl", "output": "bridge"}


def role_of(node_id):
    n = node_id.lower()
    for role, words in ROLE_WORDS:
        if any(w in n for w in words):
            return role
    return "transform"


def read_graph(g):
    """Returns a scene: objects with role, symbol, layer and order; links with conditional flags."""
    ids = [n["id"] for n in g["nodes"]]
    succ = {i: [] for i in ids}
    for e in g["edges"]:
        succ[e["source"]].append(e["target"])
    depth = {i: 0 for i in ids}
    for _ in ids:                                   # longest-path depth from the start (cycles capped)
        for e in g["edges"]:
            if depth[e["target"]] < depth[e["source"]] + 1 <= len(ids):
                depth[e["target"]] = depth[e["source"]] + 1
    objs = []
    for i in ids:
        r = role_of(i)
        objs.append({"name": i, "role": r, "kind": KIND[r], "x": depth[i], "y": LAYER[r]})
    links = [{"from": e["source"], "to": e["target"], "conditional": bool(e.get("conditional"))} for e in g["edges"]]
    return {"objects": objs, "links": links}


def patch(scene, gestures):
    """Gestures (list of (op, guest, node, place)) → graph edits a developer or tool applies to the real graph."""
    edits = []
    names = {o["name"] for o in scene["objects"]}
    for op, guest, node, place in gestures:
        if node not in names:
            raise ValueError(f"no node {node!r} in the graph")
        if op == "pierce" and place == "head":
            edits.append({"edit": "insert_before", "node": node, "new": guest})
        elif op == "pierce" and place == "heart":
            edits.append({"edit": "wrap", "node": node, "wrapper": guest})
        elif op == "pierce" and place == "brain":
            edits.append({"edit": "extend_knowledge", "node": node, "with": guest})
        elif op == "near":
            edits.append({"edit": "side_channel", "after": node, "new": guest, "affects": "successors only"})
        elif op == "grey":
            edits.append({"edit": "sandbox", "node": node, "on_error": "escalate"})
        else:
            raise ValueError(f"unknown gesture {op}/{place}")
    return edits
