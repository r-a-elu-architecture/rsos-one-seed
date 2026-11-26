"""R-003: re-implementation of C1-EXP-003 (spatial functional composition). See PREREGISTRATION_DAY2.md."""

import numpy as np

from common import world_of, bootstrap_ci, save
from rsoslang.runtime import grid_modules, random_env, shifted_env
from rsoslang.runtime.codec import encode, decode, relabel

BASE = "OBJECT a\nOBJECT b\nPLACE a X 0 Y 0\nPLACE b X 2.5 Y 0\n"
PROGRAMS = {
    "O": BASE,
    "M": BASE + "MOVE b ONTO a\n",
    "P": BASE + "PIERCE b THROUGH a\n",
    "MP": BASE + "MOVE b ONTO a\nPIERCE b THROUGH a\n",
    "MA": BASE + "MOVE b ONTO a\nATTACH b TO a\n",
}


def one_world(seed):
    rng = np.random.default_rng(seed)
    lay = {"a": grid_modules(rng), "b": grid_modules(rng)}
    env = random_env(rng)
    unseen = shifted_env(env, rng)
    out, ablated, free = {}, {}, {}
    for k, body in PROGRAMS.items():
        w = world_of(body, lay, seed)
        out[k] = w.execute(unseen)
        free[k] = w.execute(unseen, link_cost=0)
        w.cross = False
        ablated[k] = w.execute(unseen)
    inter = out["MP"] - out["M"] - out["P"] + out["O"]
    inter_abl = ablated["MP"] - ablated["M"] - ablated["P"] + ablated["O"]
    inter_free = free["MP"] - free["M"] - free["P"] + free["O"]
    return out, inter, inter_abl, inter_free


def rotation_vs_edit(n=256):
    changed = []
    for i in range(n):
        rng = np.random.default_rng(10_000 + i)
        lay = {"a": grid_modules(rng), "b": grid_modules(rng)}
        dx, dy = rng.uniform(-0.5, 0.5, size=2)
        body = f"OBJECT a\nOBJECT b\nPLACE a X 0 Y 0\nPLACE b X {dx:.3f} Y {dy:.3f}\nPIERCE b THROUGH a\n"
        rot = f"OBJECT a\nOBJECT b\nPLACE a X 0 Y 0\nPLACE b X {dx:.3f} Y {dy:.3f} ROT 90\nPIERCE b THROUGH a\n"
        w0, w1 = world_of(body, lay, i), world_of(rot, lay, i)
        changed.append(len(w0.link_set() ^ w1.link_set()))
    return changed


def codec_check(n=256):
    ok_roundtrip = ok_relabel = 0
    for i in range(n):
        rng = np.random.default_rng(20_000 + i)
        lay = {"a": grid_modules(rng), "b": grid_modules(rng)}
        dx = rng.uniform(-0.5, 0.5)
        w = world_of(f"OBJECT a\nOBJECT b\nPLACE b X {dx:.3f} Y 0\nPIERCE b THROUGH a\n", lay, i)
        env = random_env(rng)
        u = w.execute(env)
        rec, book = encode(w)
        ok_roundtrip += decode(rec, book).execute(env) == u
        rec2, book2 = relabel(rec, book, rng)
        ok_relabel += decode(rec2, book2).execute(env) == u
    return ok_roundtrip, ok_relabel


def main():
    rows = [one_world(s) for s in range(40)]
    inter = [r[1] for r in rows]
    inter_abl = [r[2] for r in rows]
    utils = {k: [r[0][k] for r in rows] for k in PROGRAMS}
    pierce_vs_attach = [r[0]["MP"] - r[0]["MA"] for r in rows]
    rot = rotation_vs_edit()
    rt, rl = codec_check()
    summary = {
        "H1_interaction": {"mean": float(np.mean(inter)), "ci95": bootstrap_ci(inter),
                           "positive": int(sum(i > 0 for i in inter)), "negative": int(sum(i < 0 for i in inter)),
                           "n": 40, "pass_rule": ">= 30 of 40 positive",
                           "pass": bool(sum(i > 0 for i in inter) >= 30)},
        "H1b_nonadditive_any_sign": {"abs_mean": float(np.mean(np.abs(inter))),
                                     "nonzero": int(sum(abs(i) > 1e-9 for i in inter))},
        "posthoc_interaction_without_link_cost": {
            "note": "not pre-registered: the functional term alone, without the 0.002 cost per link",
            "mean": float(np.mean([r[3] for r in rows])), "ci95": bootstrap_ci([r[3] for r in rows]),
            "positive": int(sum(r[3] > 0 for r in rows))},
        "H2_ablation": {"zero": int(sum(abs(i) < 1e-12 for i in inter_abl)), "n": 40,
                        "pass": bool(all(abs(i) < 1e-12 for i in inter_abl))},
        "H3_pierce_vs_attach": {"different": int(sum(abs(d) > 1e-9 for d in pierce_vs_attach)),
                                "pierce_higher": int(sum(d > 0 for d in pierce_vs_attach)),
                                "mean_diff": float(np.mean(pierce_vs_attach)), "ci95": bootstrap_ci(pierce_vs_attach),
                                "pass": bool(sum(abs(d) > 1e-9 for d in pierce_vs_attach) >= 38)},
        "H4_rotation": {"median_links_changed": float(np.median(rot)), "min": int(min(rot)), "max": int(max(rot)),
                        "explicit_edit": 1, "n": len(rot), "pass": bool(np.median(rot) > 1)},
        "H5_codec": {"roundtrip": rt, "relabel": rl, "n": 256, "pass": bool(rt == 256 and rl == 256)},
        "mean_utility": {k: float(np.mean(v)) for k, v in utils.items()},
        "chat_reference": {"interaction_mean": 0.1825, "positive": "40/40", "rotation_median": 46,
                           "reconstruction": "256/256"},
    }
    path, digest = save("R-003", {"summary": summary, "per_world": {"interaction": inter, "utilities": utils,
                                                                     "pierce_minus_attach": pierce_vs_attach},
                                  "rotation_links_changed": rot})
    print(path, digest)
    for k, v in summary.items():
        print(k, v)


if __name__ == "__main__":
    main()
