"""R-004: re-implementation of C1-EXP-004 (multi-level visual programming). See PREREGISTRATION_DAY2.md."""

import numpy as np

from common import world_of, bootstrap_ci, save
from rsoslang.runtime import random_env, shifted_env, K
from rsoslang.runtime.model import Module

SCENE = ("OBJECT grass\nOBJECT sky\nOBJECT car\nOBJECT road\n"
         "PLACE grass X -1.5 Y 0\nPLACE sky X -0.5 Y 0.9\nPLACE car X 0.6 Y 0\nPLACE road X 0.6 Y -0.9\n")


def layout(rng):
    def m(name, depth, xy):
        return Module(name, "", depth, xy, rng.normal(size=K))
    return {
        "grass": [m("", 0, (0, 0)), m("top", 0, (0, 0.2))],
        "sky": [m("", 0, (0, 0))],
        "car": [m("", 0, (0, 0)), m("engine", 1, (-0.2, 0.0)), m("seat", 1, (0.05, 0.05)), m("window", 1, (0.1, 0.25))],
        "road": [m("", 0, (0, 0)), m("white_line", 0, (0.3, 0))],
    }


TRI = "ENTER car DEPTH 1\nREGION r SHAPE triangle CENTER car SIZE 0.4 INCLUDES engine, seat, window\n"
PT = "ENTER car DEPTH 1\nREGION r SHAPE point CENTER car SIZE 0.4\n"
VARIANTS = {
    "none": SCENE,
    "triangle": SCENE + TRI + "LINE l THROUGH grass.top, sky, r, road.white_line\n",
    "point": SCENE + PT + "LINE l THROUGH grass.top, sky, r, road.white_line\n",
    "whole_car": SCENE + "LINE l THROUGH grass.top, sky, car, road.white_line\n",
    "reversed": SCENE + TRI + "LINE l THROUGH road.white_line, r, sky, grass.top\n",
}


def variants_test():
    rows = []
    for s in range(40):
        rng = np.random.default_rng(s)
        lay = layout(rng)
        thermal = random_env(rng, "thermal")
        u = {k: world_of(b, lay, s).execute(thermal, sinks_only=True) for k, b in VARIANTS.items()}
        rows.append({k: u[k] - u["none"] for k in VARIANTS if k != "none"})
    w = world_of(VARIANTS["triangle"], layout(np.random.default_rng(0)), 0)
    n_links = len([l for l in w.links if l.kind == "line"])
    return rows, n_links


# ---- program search (H9) ---------------------------------------------------------------------------
POINTS = ["grass", "grass.top", "sky", "car", "car.engine", "car.seat", "car.window", "road", "road.white_line",
          "R:triangle:0.4", "R:triangle:0.2", "R:square:0.3"]


def program(genes):
    pts, reverse, enter = genes
    body = SCENE + ("ENTER car DEPTH 1\n" if enter else "")
    names = []
    for i, p in enumerate(pts):
        if p.startswith("R:"):
            _, shape, size = p.split(":")
            body += f"REGION r{i} SHAPE {shape} CENTER car SIZE {size}\n"
            names.append(f"r{i}")
        else:
            names.append(p)
    if reverse:
        names = names[::-1]
    body += f"LINE l THROUGH {', '.join(names)}\n"
    return body


def random_genes(rng):
    return ([POINTS[i] for i in rng.choice(len(POINTS), 4, replace=False)], bool(rng.integers(2)), bool(rng.integers(2)))


def mutate(g, rng):
    pts, rev, ent = list(g[0]), g[1], g[2]
    r = rng.integers(3)
    if r == 0:
        i = rng.integers(4)
        choices = [p for p in POINTS if p not in pts]
        pts[i] = choices[rng.integers(len(choices))]
    elif r == 1:
        rev = not rev
    else:
        ent = not ent
    return (pts, rev, ent)


def score(g, lay, envs, seed):
    w = world_of(program(g), lay, seed)
    return float(np.mean([w.execute(e, sinks_only=True) for e in envs]))


def descriptor(g, lay, seed):
    w = world_of(program(g), lay, seed)
    nsel = len({l.dst for l in w.links} | {l.src for l in w.links})
    return (min(nsel // 3, 3), int(g[2]))


def search(method, seed, budget=180):
    rng = np.random.default_rng(1000 + seed)
    lay = layout(np.random.default_rng(seed))
    train = [random_env(np.random.default_rng(5000 + seed * 10 + i)) for i in range(3)]
    mean_env = train[0]
    held = shifted_env(mean_env, np.random.default_rng(9000 + seed), shift=0.8, name="held_out")
    evaluated = []
    if method == "random":
        for _ in range(budget):
            g = random_genes(rng)
            evaluated.append((score(g, lay, train, seed), g))
    elif method == "evolution":
        best = random_genes(rng)
        bs = score(best, lay, train, seed)
        evaluated.append((bs, best))
        for _ in range(budget - 1):
            c = mutate(best, rng)
            cs = score(c, lay, train, seed)
            evaluated.append((cs, c))
            if cs >= bs:
                best, bs = c, cs
    elif method == "archive":
        archive = {}
        for i in range(budget):
            if i < 20 or not archive:
                g = random_genes(rng)
            else:
                keys = list(archive)
                g = mutate(archive[keys[rng.integers(len(keys))]][1], rng)
                if rng.random() < 0.2:
                    g = random_genes(rng)       # periodically explore new branches
            s = score(g, lay, train, seed)
            evaluated.append((s, g))
            d = descriptor(g, lay, seed)
            if d not in archive or s > archive[d][0]:
                archive[d] = (s, g)
    best_train, best = max(evaluated, key=lambda t: t[0])
    w = world_of(program(best), lay, seed)
    return {"train": best_train, "held_out": float(w.execute(held, sinks_only=True)), "best": program(best).split("\n")[-2]}


def main():
    rows, n_links = variants_test()
    d = {k: [r[k] for r in rows] for k in rows[0]}
    tri_pt = [a - b for a, b in zip(d["triangle"], d["point"])]
    tri_whole = [a - b for a, b in zip(d["triangle"], d["whole_car"])]
    fwd_rev = [a - b for a, b in zip(d["triangle"], d["reversed"])]
    res = {m: [search(m, s) for s in range(12)] for m in ("random", "evolution", "archive")}
    ho = {m: [r["held_out"] for r in v] for m, v in res.items()}
    diff = [a - b for a, b in zip(ho["archive"], ho["random"])]
    summary = {
        "program_links": {"selection_points": 4, "line_links": n_links, "property_assignments": n_links * K,
                          "chat": "4 points -> 7 links -> 49 properties"},
        "mean_change_vs_no_program": {k: float(np.mean(v)) for k, v in d.items()},
        "H6_triangle_gt_point": {"wins": int(sum(x > 0 for x in tri_pt)), "n": 40, "mean": float(np.mean(tri_pt)),
                                 "ci95": bootstrap_ci(tri_pt), "pass": bool(sum(x > 0 for x in tri_pt) >= 30)},
        "H7_internal_gt_whole": {"wins": int(sum(x > 0 for x in tri_whole)), "n": 40, "mean": float(np.mean(tri_whole)),
                                 "ci95": bootstrap_ci(tri_whole), "pass": bool(sum(x > 0 for x in tri_whole) >= 30)},
        "H8_forward_gt_reversed": {"wins": int(sum(x > 0 for x in fwd_rev)), "n": 40, "mean": float(np.mean(fwd_rev)),
                                   "ci95": bootstrap_ci(fwd_rev), "pass": bool(sum(x > 0 for x in fwd_rev) >= 30)},
        "H9_search": {"held_out_mean": {m: float(np.mean(v)) for m, v in ho.items()},
                      "archive_minus_random": {"mean": float(np.mean(diff)), "ci95": bootstrap_ci(diff),
                                               "wins": int(sum(x > 0 for x in diff)), "n": 12},
                      "pass": bool(sum(x > 0 for x in diff) >= 9 and bootstrap_ci(diff)[0] > 0)},
        "chat_reference": {"triangle": 0.107775, "point": -0.0075, "whole_car": -0.0075, "reversed": -0.0175,
                           "archive_minus_random": "+0.0399, 12/12"},
    }
    path, digest = save("R-004", {"summary": summary, "per_world": d, "search": res})
    print(path, digest)
    for k, v in summary.items():
        print(k, v)


if __name__ == "__main__":
    main()
