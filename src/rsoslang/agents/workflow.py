"""A 12-module agent workflow with addressable parts, so the painting's gestures have exact program meanings.

Every node has four places a guest module can be put (owner, round 3: "each of the places will have different
result"):
  head   before the node: on its input (attention, alert)
  heart  inside the node's execution: wraps how it works
  brain  in the node's knowledge: its lexicon, tables, parameters
  near   beside the node: acts on what flows on to its neighbours, not on the node itself
"""

import copy
import random
import re
from dataclasses import dataclass, field

from .tickets import knowledge_base, REFUND_LIMIT, CATEGORIES


@dataclass
class Node:
    name: str
    role: str
    layer: int                     # 0 = top (supervisory) … 3 = bottom (input/output, infrastructure)
    cost: float
    knowledge: dict = field(default_factory=dict)
    head: list = field(default_factory=list)
    heart: list = field(default_factory=list)
    brain: list = field(default_factory=list)      # guests learned into the knowledge (shown on the painting)
    near: list = field(default_factory=list)
    sandboxed: bool = False
    retries: int = 0

    def run(self, fn, state, ctx):
        for g in self.head:
            g.at_head(self, state, ctx)
        call = fn
        for g in self.heart:
            call = g.at_heart(self, call)
        if self.sandboxed:
            inner = call

            def call(n, s, c, inner=inner):
                try:
                    return inner(n, s, c)
                except ToolCrash:
                    c["contained"] += 1
                    s["action"] = "escalate"
                    return s
        state = call(self, state, ctx)
        for g in self.near:
            g.at_near(self, state, ctx)
        ctx["cost"] += self.cost
        ctx["visits"][self.name] = ctx["visits"].get(self.name, 0) + 1
        return state


class ToolCrash(Exception):
    pass


# ---- the twelve node functions ----------------------------------------------------------------------
def f_intake(n, s, c):
    s["text"] = s["ticket"]["text"]
    return s


def f_normalize(n, s, c):
    s["text"] = re.sub(r"[^\w\s.]", " ", s["text"].lower())
    return s


def f_classify(n, s, c):
    text = s["text"]
    best, hits = "other", 0
    for cat, words in n.knowledge["lexicon"].items():
        h = sum(1 for w in words if w in text)
        if h > hits:
            best, hits = cat, h
    s["category"] = best
    return s


def f_extract(n, s, c):
    m = re.search(r"amount (\d+(?:\.\d+)?)", s["text"])
    s["amount"] = float(m.group(1)) if m else 0.0
    m = re.search(r"\bc(\d{4})\b", s["text"])
    s["customer"] = f"C{m.group(1)}" if m else None
    return s


def f_memory(n, s, c):
    s["tier"] = n.knowledge["kb"].get(s["customer"], "bronze")
    c["cost"] += n.knowledge.get("lookup_cost", 3.0)
    return s


def f_priority(n, s, c):
    s["priority"] = "high" if s["tier"] == "gold" or s["amount"] > 200 else "normal"
    return s


ACTIONS = {cat: spec["action"] for cat, spec in CATEGORIES.items()}


def f_plan(n, s, c):
    s["action"] = ACTIONS.get(s["category"], "escalate")
    return s


def f_policy(n, s, c):
    if s["action"] == "refund" and s["amount"] > REFUND_LIMIT[s["tier"]]:
        s["action"] = "escalate"
    return s


def f_act(n, s, c):
    r = random.Random(f"{c['seed']}:{s['ticket']['id']}:{c['visits'].get('act', 0)}")
    x = r.random()
    if x < 0.05:
        raise ToolCrash("tool crashed")
    s["tool_ok"] = x >= 0.20                  # 15% of calls fail softly
    return s


def f_verify(n, s, c):
    s["verified"] = s.get("tool_ok", False)
    return s


def f_respond(n, s, c):
    s["response"] = s["action"] if s.get("verified") else "escalate"
    return s


def f_log(n, s, c):
    c["log"].append((s["ticket"]["id"], s.get("category"), s.get("response")))
    return s


FUNCS = {"intake": f_intake, "normalize": f_normalize, "classify": f_classify, "extract": f_extract,
         "memory": f_memory, "priority": f_priority, "plan": f_plan, "policy": f_policy, "act": f_act,
         "verify": f_verify, "respond": f_respond, "log": f_log}
ORDER = list(FUNCS)


def build():
    lex = {cat: list(spec["words"]) for cat, spec in CATEGORIES.items()}
    nodes = {
        "intake": Node("intake", "input", 3, 0.5),
        "normalize": Node("normalize", "transform", 2, 0.5),
        "classify": Node("classify", "reason", 1, 1.0, {"lexicon": lex}),
        "extract": Node("extract", "transform", 2, 1.0),
        "memory": Node("memory", "memory", 2, 0.5, {"kb": knowledge_base(), "lookup_cost": 3.0}),
        "priority": Node("priority", "reason", 1, 0.5),
        "plan": Node("plan", "reason", 1, 1.0),
        "policy": Node("policy", "policy", 0, 0.5),
        "act": Node("act", "tool", 2, 2.0, retries=1),
        "verify": Node("verify", "check", 1, 0.5),
        "respond": Node("respond", "output", 3, 0.5),
        "log": Node("log", "output", 3, 0.2),
    }
    return Workflow(nodes)


class Workflow:
    def __init__(self, nodes):
        self.nodes = nodes
        self.order = list(ORDER)

    def copy(self):
        return copy.deepcopy(self)

    def run_ticket(self, t, ctx):
        s = {"ticket": t}
        for name in self.order:
            n = self.nodes[name]
            if name == "act":                     # the core loop: act → verify, retried
                for attempt in range(1 + n.retries):
                    s = n.run(FUNCS["act"], s, ctx)
                    if s.get("tool_ok"):
                        break
                continue
            s = n.run(FUNCS[name], s, ctx)
        return s

    def evaluate(self, tickets, seed=0):
        ctx = {"cost": 0.0, "visits": {}, "log": [], "seed": seed, "contained": 0, "cache": {}}
        correct = crashed = 0
        per_node_err = {}
        for t in tickets:
            expected = t["action"]
            if t["category"] == "billing":
                tier = knowledge_base().get(t["customer"], "bronze")
                if t["amount"] > REFUND_LIMIT[tier]:
                    expected = "escalate"
            try:
                s = self.run_ticket(t, ctx)
            except ToolCrash:
                crashed += 1
                per_node_err["act"] = per_node_err.get("act", 0) + 1
                continue
            if s.get("category") != t["category"]:
                per_node_err["classify"] = per_node_err.get("classify", 0) + 1
            ok = s.get("category") == t["category"] and s.get("response") == expected
            correct += ok
        n = len(tickets)
        return {"accuracy": correct / n, "crashed": crashed / n, "cost_per_ticket": ctx["cost"] / n,
                "contained": ctx["contained"], "visits": ctx["visits"], "errors": per_node_err,
                "score": correct / n - 0.01 * ctx["cost"] / n}
