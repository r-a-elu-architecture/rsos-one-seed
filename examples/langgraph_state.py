"""RSOS State Runtime as LangGraph nodes: a multi-agent loop over shared state in 1 model call instead of one per step.

A typical LangGraph workflow calls the model once per change request, because each step must read what the previous
step wrote. Here the planner node calls the model ONCE for all requests; the runtime node executes the operations
(the runtime computes every value); each agent node keeps its own copy and heals it against the green dot with zero
model calls.

    pip install rsoslang langgraph
    python examples/langgraph_state.py                 # offline demo with a scripted model reply
    RSOS_MODEL=claude-haiku-5-5 python examples/langgraph_state.py   # with a real model (pip install anthropic)

The node functions are plain functions (dict in, dict out), so they also work without LangGraph: the script falls
back to calling them in order when langgraph is not installed.
"""

import json
import os
from typing import TypedDict

from rsoslang.state import Ledger, parse_plan, plan_prompt


class Flow(TypedDict, total=False):
    state: dict           # the agreed shared state (owned by the runtime)
    requests: list        # all change requests of the task
    plan: dict            # {step: operations}, written by the model once
    copies: dict          # each agent's own copy
    report: dict          # what the runtime did
    model_calls: int


def call_model(system: str, user: str) -> str:
    """One model call. Replace with your own client; RSOS_MODEL uses the Anthropic SDK."""
    model = os.environ.get("RSOS_MODEL")
    if not model:   # offline demo: the reply a model gives for the three requests below
        return ("#0\nINHERIT auth.timeout_ms auth.timeout_ms +100\n"
                "#1\nFUSE auth.retries auth.retries search.retries CAP 8\n"
                "#2\nROUTE auth.region = eu : search.region eu | us")
    import anthropic
    msg = anthropic.Anthropic().messages.create(model=model, max_tokens=1024, system=system,
                                                messages=[{"role": "user", "content": user}])
    return msg.content[0].text


def planner(f: Flow) -> Flow:
    p = plan_prompt(f["requests"], f["state"])
    return {"plan": parse_plan(call_model(p["system"], p["user"])), "model_calls": f.get("model_calls", 0) + 1}


def runtime(f: Flow) -> Flow:
    led = Ledger(f["state"])
    out = led.apply_plan(f["plan"])
    return {"state": led.state, "report": {"dot": out["dot"], "failed": out["failed"]}}


def agents(f: Flow) -> Flow:
    """Every agent's copy is checked against the green dot and healed from the agreed state: 0 model calls."""
    led = Ledger(f["state"])
    copies = dict(f.get("copies") or {})
    healed = {}
    for name, copy in copies.items():
        r = led.sync(copy)
        copies[name], healed[name] = r["state"], r["healed"]
    return {"copies": copies, "report": {**f.get("report", {}), "synced": healed}}


def build_graph():
    from langgraph.graph import END, START, StateGraph
    g = StateGraph(Flow)
    g.add_node("planner", planner)
    g.add_node("runtime", runtime)
    g.add_node("agents", agents)
    g.add_edge(START, "planner")
    g.add_edge("planner", "runtime")
    g.add_edge("runtime", "agents")
    g.add_edge("agents", END)
    return g.compile()


def run(flow: Flow) -> Flow:
    try:
        return build_graph().invoke(flow)
    except ImportError:                       # no langgraph: the same nodes, in order
        for node in (planner, runtime, agents):
            flow = {**flow, **node(flow)}
        return flow


if __name__ == "__main__":
    start = {"auth.timeout_ms": "700", "auth.retries": "3", "auth.region": "eu", "search.retries": "6",
             "search.region": "us"}
    drifted_worker = {**start, "auth.retries": "2"}          # a worker whose copy went wrong
    result = run({"state": start,
                  "requests": ["Raise the auth timeout by 100",
                               "Set auth retries to auth retries plus search retries, at most 8",
                               "If auth region is eu, set search region to eu, otherwise us"],
                  "copies": {"worker": drifted_worker, "checker": dict(start)}})
    print(json.dumps({"model_calls": result["model_calls"], "state": result["state"], "report": result["report"]},
                     indent=1))
