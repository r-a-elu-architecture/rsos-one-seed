"""The discovery engine (T9): search over placements, removal test, induction of a placement rule, transfer."""
import itertools

from .painting.scene import apply

CHOICES = {"spell_corrector": [None, "head", "heart", "brain", "near"],
           "synonym_expander": [None, "head", "heart", "brain", "near"],
           "cache": [None, "head", "heart", "brain"], "fast_retry": [None, "heart"],
           "grey": [None, "on"], "heal": [None, "on"]}
TARGET = {"spell_corrector": "classify", "synonym_expander": "classify", "cache": "memory", "fast_retry": "act"}


def program(cfg):
    out = []
    for g, p in cfg.items():
        if not p:
            continue
        if g == "grey":
            out.append("SHIFT act TO grey")
        elif g == "heal":
            out.append("HEAL act")
        elif p == "near":
            out.append(f"PLACE {g} NEAR {TARGET[g]}")
        else:
            out.append(f"PIERCE {g} THROUGH {TARGET[g]}.{p}")
    return "\n".join(out) + ("\n" if out else "")


def score(base, cfg, tickets, seed):
    wf, _ = apply(base, program(cfg))
    return wf.evaluate(tickets, seed)["score"]


def search(base, tickets, seed):
    results = []
    for combo in itertools.product(*CHOICES.values()):
        cfg = dict(zip(CHOICES, combo))
        results.append((score(base, cfg, tickets, seed), cfg))
    results.sort(key=lambda t: -t[0])
    return results


def removal(base, cfg, tickets, seed):
    full = score(base, cfg, tickets, seed)
    out = {}
    for g, p in cfg.items():
        if p:
            c2 = dict(cfg, **{g: None})
            out[f"{g}={p}"] = round(full - score(base, c2, tickets, seed), 4)
    return out


def induce(results):
    """For each guest, the place with the highest mean score across all searched programs: a placement rule."""
    rule = {}
    for g, places in CHOICES.items():
        best = max(places, key=lambda p: sum(s for s, c in results if c[g] == p) / max(1, sum(1 for _, c in results if c[g] == p)))
        rule[g] = best
    return rule
