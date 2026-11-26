"""E1: metric spheres under the White Dragon's light. Pre-registration: experiments/PREREGISTRATION_E1.md."""

import json

import numpy as np

from common import save
from rsoslang import dragon as D

SEEDS, BUDGET = 200, 20


def particle_run(spheres, entries, rng, weighted):
    w = np.array([D.deficit(b) for b in spheres]) if weighted else np.ones(len(spheres))
    p = w / w.sum()
    gain = 0.0
    for _ in range(BUDGET):
        b = spheres[rng.choice(len(spheres), p=p)]
        kids = [D.land(b, e, s) for e, s in D.paths(b, entries)]
        if kids:
            best = min(kids, key=lambda c: c["deficit"])
            gain += max(0.0, D.deficit(b) - best["deficit"])
    return gain


def style_run(spheres, entries, rng, style):
    doms, defs = set(), []
    for _ in range(BUDGET):
        b = spheres[rng.integers(len(spheres))]
        opts = D.style_choice(b, entries, style)
        if not opts:
            continue
        e, s = opts[rng.integers(len(opts))]
        c = D.land(b, e, s)
        doms.add(e["domain"]); defs.append(c["deficit"])
    return len(doms), float(np.mean(defs))


def main():
    spheres, entries = D.load()
    raw, _ = D.grow(spheres, entries, 2, filtered=False)
    fil, kids = D.grow(spheres, entries, 2, filtered=True)
    g1 = kids[0]
    dom_g1 = sorted({c["domain"] for c in g1})
    lacking = [b["code"] for b in spheres if D.deficit(b) > 0]
    healed = sorted({c["parent"] for c in g1 if c["parent"] in lacking})
    unhealed = sorted(set(lacking) - set(healed))
    rng = np.random.default_rng(20261117)
    gw = [particle_run(spheres, entries, rng, True) for _ in range(SEEDS)]
    gu = [particle_run(spheres, entries, rng, False) for _ in range(SEEDS)]
    lion = [style_run(spheres, entries, rng, "lion") for _ in range(SEEDS)]
    tiger = [style_run(spheres, entries, rng, "tiger") for _ in range(SEEDS)]
    ld, lf = np.mean([x[0] for x in lion]), np.mean([x[1] for x in lion])
    td, tf = np.mean([x[0] for x in tiger]), np.mean([x[1] for x in tiger])
    # showcase: children that heal the claims (object model or non-observable relations)
    show = [c for c in g1 if D.deficit(next(b for b in spheres if b["code"] == c["parent"])) >= 0.5][:400]
    picks, used = [], set()
    for c in show:
        if c["parent"] not in used:
            used.add(c["parent"]); picks.append({k: c[k] for k in ("code", "definition", "relations", "deficit")})
    summary = {
        "spheres": len(spheres), "measures": len(entries),
        "unfiltered_sizes": raw, "filtered_sizes": fil,
        "deficit_weighted_gain": float(np.mean(gw)), "uniform_gain": float(np.mean(gu)),
        "gain_ratio": float(np.mean(gw) / np.mean(gu)),
        "domains_gen1": dom_g1, "lacking_spheres": len(lacking), "healed_gen1": len(healed), "unhealed": unhealed,
        "lion_domains": float(ld), "tiger_domains": float(td), "lion_child_deficit": float(lf),
        "tiger_child_deficit": float(tf), "healing_children": picks,
    }
    checks = {
        "P1_exponential_unfiltered": bool(raw[1] >= 3 * raw[0] and raw[2] >= 3 * raw[1]),
        "P2_bounded_but_creating": bool(0 < fil[2] < 3 * fil[1]),
        "P3_deficit_targeting": bool(summary["gain_ratio"] >= 1.5),
        "P4_domains": bool(len(dom_g1) >= 6),
        "P5_lion_tiger": bool(ld > td and tf < lf),
        "P6_heal_coverage": bool(not unhealed),
    }
    path, digest = save("e1_dragon", {"summary": summary, "checks": checks,
                                      "gen1": [{k: c[k] for k in ("code", "relations", "domain", "deficit",
                                                                    "measured_by")} for c in g1]})
    print(json.dumps({k: v for k, v in summary.items() if k != "healing_children"}, indent=1, ensure_ascii=False))
    print(json.dumps({k: bool(v) for k, v in checks.items()})); print(path, digest)
    for p in picks[:20]:
        print("-", p["definition"], "| deficit", round(p["deficit"], 2))


if __name__ == "__main__":
    main()
