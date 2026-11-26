"""Every combination of the editor's gestures, run on held-out A, so the browser editor shows measured effects."""
import itertools
import json
import os

from common import ROOT
from rsoslang.agents.workflow import build
from rsoslang.agents.tickets import make_tickets
from rsoslang.painting.scene import apply

A = make_tickets(500, 2, typo_rate=0.3, unseen_rate=0.3)
CHOICES = {"spell_corrector": [None, "head", "heart", "brain", "near"],
           "synonym_expander": [None, "head", "heart", "brain", "near"],
           "cache": [None, "head", "heart", "brain"], "fast_retry": [None, "heart"],
           "grey": [None, "on"], "heal": [None, "on"]}
TARGET = {"spell_corrector": "classify", "synonym_expander": "classify", "cache": "memory", "fast_retry": "act"}


def program(cfg):
    lines = []
    for g, place in cfg.items():
        if place is None:
            continue
        if g == "grey":
            lines.append("SHIFT act TO grey")
        elif g == "heal":
            lines.append("HEAL act")
        elif place == "near":
            lines.append(f"PLACE {g} NEAR {TARGET[g]}")
        else:
            lines.append(f"PIERCE {g} THROUGH {TARGET[g]}.{place}")
    return "\n".join(lines) + ("\n" if lines else "")


def key(cfg):
    return "|".join(f"{g}={cfg[g] or '-'}" for g in CHOICES)


base = build()
table = {}
for combo in itertools.product(*CHOICES.values()):
    cfg = dict(zip(CHOICES, combo))
    wf, _ = apply(base, program(cfg))
    r = wf.evaluate(A, 2)
    table[key(cfg)] = {k: round(r[k], 4) for k in ("accuracy", "crashed", "cost_per_ticket", "score")}
with open(os.path.join(ROOT, "results", "editor_table.json"), "w") as f:
    json.dump({"choices": CHOICES, "target": TARGET, "set": "held-out A: seed 2, 500 tickets, 30% typos, 30% unseen",
               "table": table}, f)
print(len(table))
