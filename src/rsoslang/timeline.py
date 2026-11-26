"""Time and video (T10): a run recorded as frames; play, slow, pause, rewind, cut, branch; every frame is a painting.

Chat 2 T53–T57 (owner): the video of a system with its functional properties; slow down, fast forward, pause and
analyse; a line through time programs the analysis; at every point in time the vertical cut is a painting.
"""

import copy

from .agents.workflow import FUNCS, ToolCrash
from .painting.scene import apply


def record(workflow, tickets, seed=0):
    """Run tickets and keep one frame per node visit: (ticket, node, state after the node)."""
    frames = []
    ctx = {"cost": 0.0, "visits": {}, "log": [], "seed": seed, "contained": 0, "cache": {}}
    for t in tickets:
        s = {"ticket": t}
        for name in workflow.order:
            n = workflow.nodes[name]
            try:
                s = n.run(FUNCS[name], s, ctx)
            except ToolCrash:
                frames.append({"ticket": t["id"], "node": name, "state": "crashed"})
                break
            frames.append({"ticket": t["id"], "node": name,
                           "state": {k: v for k, v in s.items() if k in ("category", "amount", "customer", "tier", "action",
                                                                        "tool_ok", "response")}})
    return frames


def play(frames, start=0, rate=1.0, n=10):
    """Frames shown from `start`; rate < 1 shows every frame (slow), rate > 1 skips (fast forward)."""
    step = max(1, int(round(rate)))
    return frames[start: start + n * step: step]


def pause_at(frames, node, ticket=None):
    return [i for i, f in enumerate(frames) if f["node"] == node and (ticket is None or f["ticket"] == ticket)]


def rewind(frames, i, k=1):
    return frames[max(0, i - k): i + 1][::-1]


def cut(frames, a, b):
    return frames[a:b]


def branch(workflow, tickets, ticket_id, gestures, seed=0):
    """A counterfactual: the same ticket run again from the start with gestures applied."""
    wf, changes = apply(workflow, gestures)
    t = [x for x in tickets if x["id"] == ticket_id]
    return record(wf, t, seed), changes


def painting_at(frames, i):
    """The vertical cut at frame i: which node is active, and every node's last known state up to i."""
    last = {}
    for f in frames[: i + 1]:
        last[f["node"]] = f["state"]
    return {"active": frames[i]["node"], "ticket": frames[i]["ticket"], "nodes": copy.deepcopy(last)}
