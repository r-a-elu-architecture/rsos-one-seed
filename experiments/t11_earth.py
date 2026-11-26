"""T11: population → households → market on the cue framework's person simulator. See PREREGISTRATION_T11.md."""
import random

import numpy as np

from common import save, bootstrap_ci
from rsoslang.governance import load_framework
from rsoslang.identity import population

load_framework()
import importlib  # noqa: E402
sim = importlib.import_module("rsxv.sim")
world = importlib.import_module("rsxv.world")
MODES, SEG = world.PERSON_MODES, world.SEGMENT_S
CHOICE = {"calmness": "BEAR", "drive": "TIGER", "regulation": "EAGLE"}


def run(policy, k, days=90, seed=0):
    people = population(100, seed)
    bodies = []
    for i, p in enumerate(people):
        rng = random.Random(seed * 1000 + i)
        prof = sim.person(rng, i)
        bodies.append(sim.Body(prof, rng, None, sham=(policy == "sham")))
    cash = np.full(100, 300.0)
    biz = np.full(12, 2000.0)
    total0 = cash.sum() + biz.sum()
    employer = np.arange(100) % 12
    spend_total, unmet, conserved = 0.0, 0, True
    life = random.Random(seed + 7)
    for day in range(days):
        for i, b in enumerate(bodies):
            if life.random() < 0.15:
                b.s["arousal"] = min(1.0, b.s["arousal"] + 0.2)
                b.s["distress"] = min(10.0, b.s["distress"] + 1.0)
            if policy == "none":
                ops = []
            elif policy in ("sham", "fixed"):
                ops = MODES["BEAR"]
            else:
                ops = MODES["BEAR"] if b.s["distress"] >= 6 else MODES[CHOICE[people[i]["override"]]]
            for _ in range(SEG):
                b.step(ops)
        wage = np.minimum(60.0, biz[employer] / 10)              # businesses pay what they can
        np.add.at(biz, employer, -wage)
        cash += wage
        d = np.array([b.s["distress"] for b in bodies])
        want = 20 + 25 * (1 + k * (d - 5) / 5)
        pay = np.minimum(cash, want)
        unmet += int((cash < 20).sum())
        cash -= pay
        shop = np.arange(100) % 12
        np.add.at(biz, shop, pay)
        spend_total += float(np.maximum(pay - 20, 0).sum())
        conserved &= abs(cash.sum() + biz.sum() - total0) < 1e-6
    d = np.array([b.s["distress"] for b in bodies])
    a = np.array([b.s["agency"] for b in bodies])
    tension = d.reshape(25, 4).mean(axis=1) / 10
    return {"distress": d, "agency": a, "tension": float(tension.mean()), "cash_mean": float(cash.mean()),
            "discretionary": spend_total, "unmet_days": unmet, "conserved": conserved}


def main():
    out = {}
    for k in (0.3, -0.3):
        out[k] = {p: run(p, k) for p in ("none", "sham", "fixed", "adaptive")}
    r = out[0.3]
    dd = list(r["adaptive"]["distress"] - r["none"]["distress"])
    eff = {k: out[k]["adaptive"]["discretionary"] - out[k]["none"]["discretionary"] for k in out}
    summary = {
        "per_policy_k+0.3": {p: {"distress": round(float(v["distress"].mean()), 3), "agency": round(float(v["agency"].mean()), 3),
                                 "tension": round(v["tension"], 3), "cash_mean": round(v["cash_mean"], 2),
                                 "discretionary": round(v["discretionary"], 1), "unmet_days": v["unmet_days"]}
                             for p, v in r.items()},
        "H1_propagation": {"distress_adaptive_minus_none": round(float(np.mean(dd)), 3), "ci95": bootstrap_ci(dd),
                           "spending_diff": round(eff[0.3], 1),
                           "pass": bootstrap_ci(dd)[1] < 0 and abs(eff[0.3]) > 0},
        "H2_cash_conserved": {"pass": all(v["conserved"] for kk in out for v in out[kk].values())},
        "H3_sign_set_by_relation": {"k+0.3": round(eff[0.3], 1), "k-0.3": round(eff[-0.3], 1),
                                    "pass": eff[0.3] * eff[-0.3] < 0},
        "H4_fixed_vs_adaptive": {"distress": [round(float(r["fixed"]["distress"].mean()), 3), round(float(r["adaptive"]["distress"].mean()), 3)],
                                 "agency": [round(float(r["fixed"]["agency"].mean()), 3), round(float(r["adaptive"]["agency"].mean()), 3)]},
    }
    path, digest = save("T11-EARTH", {"summary": summary})
    print(path, digest)
    for kk, v in summary.items():
        print(kk, v)


if __name__ == "__main__":
    main()
