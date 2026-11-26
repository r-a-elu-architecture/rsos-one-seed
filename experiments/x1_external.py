"""X1: an external system (the cue framework's agent repair loop) painted and steered by RSOS meanings."""
import importlib
import random

import numpy as np

from common import compile_source, save, bootstrap_ci
from rsoslang.governance import load_framework
from rsoslang.painting.graphs import read_graph

load_framework()
arc = importlib.import_module("rsxv.archetypes")

STRATEGY = {"interface_only": lambda s, b: arc.local_repair(s, b),
            "lateral": lambda s, b: arc.local_repair(s, b, blame_upstream=True),
            "supervisory_entry": lambda s, b: arc.meta_repair(s, b)}


def meaning_of(side):
    src = f"LANGUAGE RSOS 0.2\nWORLD w\nOBJECT observer\nOBJECT system\nTOUCH observer ON system AT {side}\n"
    res = compile_source(src)
    assert res.ok
    return [o for o in res.ir["ops"] if o["op"] == "touch"][0]["meanings"][0]["value"]


def faults(seed):
    rng = random.Random(seed)
    sys_ = arc.AgentSystem(random.Random(seed + 1))
    for _ in range(rng.randint(1, 2)):
        sys_.inject(rng.choice(list(arc.GRAPH)), rng.choice(arc.MODULES), 0.8, silent=rng.random() < 0.5)
    return sys_


def main():
    graph = {"nodes": [{"id": a} for a in arc.GRAPH],
             "edges": [{"source": u, "target": a} for a, ins in arc.GRAPH.items() for u in ins]}
    scene = read_graph(graph)
    res = {}
    for side in ("surface", "side", "top"):
        m = meaning_of(side)
        runs = [STRATEGY[m](faults(s), 6) for s in range(300)]
        res[side] = {"meaning": m, "fixed": [float(r["fixed"]) for r in runs], "health": [r["health"] for r in runs],
                     "used": [r["used"] for r in runs]}
    rate = {k: float(np.mean(v["fixed"])) for k, v in res.items()}
    health = {k: float(np.mean(v["health"])) for k, v in res.items()}
    d_top_surface = [a - b for a, b in zip(res["top"]["fixed"], res["surface"]["fixed"])]
    summary = {
        "painted_scene": {o["name"]: o["kind"] for o in scene["objects"]},
        "meanings": {k: v["meaning"] for k, v in res.items()},
        "fixed_rate": rate, "health": health,
        "budget_used": {k: float(np.mean(v["used"])) for k, v in res.items()},
        "H1_distinct": {"pass": len({round(x, 3) for x in rate.values()}) == 3 or len({round(x, 3) for x in health.values()}) == 3},
        "H2_top_beats_surface": {"diff": float(np.mean(d_top_surface)), "ci95": bootstrap_ci(d_top_surface),
                                 "pass": bootstrap_ci(d_top_surface)[0] > 0},
        "H3_top_vs_side": {"top": rate["top"], "side": rate["side"]},
    }
    path, digest = save("X1-EXTERNAL", {"summary": summary})
    print(path, digest)
    for k, v in summary.items():
        print(k, v)


if __name__ == "__main__":
    main()
