"""ENGINE1: the seed evolution engine (Root Genome, six children, Father, Mother, generator, Law 0, champion challenge).
Predictions: PREREG_ENGINE1.md (sha256 2c693578…db12f, commit 952c928), sealed before this file."""
import copy
import hashlib
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "roots")))
import t2c as H  # noqa: E402

CAL, REP, HOLD = range(800, 804), range(804, 808), range(940, 948)
BUDGET = 45
CHILDREN = ["Tiger", "Lion", "Leopard", "Bear", "Dragon", "WhiteDragon"]

# ------------------------------------------------------------------------------------------------ primitives (safe ranges)
SPACE = {
    "passes": (1, 5, "int"), "sigma_mult": (0.25, 4.0, "float"), "eps": (0.001, 0.2, "float"),
    "gate": (0.0, 1.0, "float"), "c": (0.5, 4.0, "float"), "r6": (0, 1, "int"),
    "margin": (0.0, 3.0, "float"), "rounds": (1, 3, "int"), "mode": (0, 3, "int"),
}
TARGET_KEYS = {
    "T1": ["passes", "sigma_mult", "eps", "c", "r6", "margin", "rounds"],
    "T2": ["passes", "sigma_mult", "eps", "gate", "c", "r6"],
    "T3": ["passes", "sigma_mult", "eps", "c", "mode"],
}
INCUMBENT = {
    "T1": {"passes": 5, "sigma_mult": 1.0, "eps": 0.01, "c": 2.0, "r6": 1, "margin": 1.0, "rounds": 1},
    "T2": {"passes": 5, "sigma_mult": 1.0, "eps": 0.01, "gate": 0.9, "c": 2.0, "r6": 1},
    "T3": {"passes": 3, "sigma_mult": 1.0, "eps": 0.01, "c": 2.0, "mode": 0},
}
MARGIN = {"T1": 0.10, "T2": 0.02, "T3": 0.10}


def law0(cand):
    for k, v in cand.items():
        lo, hi, kind = SPACE[k]
        if not (lo <= v <= hi) or (kind == "int" and int(v) != v):
            return False
    return True


# ------------------------------------------------------------------------------------------------ hosts (cached stores)
STORE = {}


def store(seed, r6):
    key = (seed, r6)
    if key not in STORE:
        fo, ff, fv = H.facts(seed)
        arm = dict(codes="rand", r6=bool(r6), heal=False, gate=False)
        R, codes, h = H.holo_store(arm, fo, ff, fv)
        STORE[key] = (ff, fv, R, codes, h)
    return STORE[key]


def read(cand, h, alive, R, ff, codes, use_gate):
    H.EPS = cand["eps"]
    hd = h * alive.astype(np.int8)
    v, gap, sup = H.plain_read(hd, R, ff, codes)
    weak = gap < cand["c"] * np.sqrt(np.maximum(sup, 1))
    n_low = int(weak.sum())
    held = use_gate and n_low > cand["gate"] * len(ff)
    sigma = cand["sigma_mult"] * np.sqrt(2 * n_low + 1)
    ones = np.ones(len(ff), np.int32)
    w = ones
    for _ in range(int(cand["passes"]) - 1 if cand["passes"] > 1 else 0):
        w = H.writer_weights(R, ff, v, codes) if (cand.get("r6", 0) and not held) else ones
        vn = H.explain_read(hd, alive.astype(np.float32), R, ff, codes, v, w, sigma)
        if np.array_equal(vn, v):
            break
        v = vn
    H.EPS = 0.01
    return v, w, weak


def eval_T1(cand, seeds):
    on = land = flipped = 0
    for s in seeds:
        ff, fv, R, codes, h = store(s, 1)
        g = np.random.default_rng([s, 202])
        fl = np.zeros(H.D, bool); fl[g.choice(H.D, H.D // 10, replace=False)] = True
        hf = h.copy(); hf[fl] *= -1
        landed = np.zeros(H.D, bool)
        for _ in range(int(cand["rounds"])):
            v, w, _ = read(cand, hf, np.ones(H.D, bool), R, ff, codes, False)
            S = (w @ H.bindings(R, ff, v, codes).astype(np.int32)).astype(np.float64)
            rec = H.sgn(S)
            need = (rec != hf) & (np.abs(S) >= cand["margin"] * S.std()) & ~landed
            hf[need] = rec[need]; landed |= need
        on += int((landed & fl).sum()); land += int(landed.sum()); flipped += int(fl.sum())
    prec = on / land if land else 1.0; rec_ = on / flipped
    return (rec_ if prec >= 0.99 else rec_ - 1.0), {"precision": round(prec, 5), "recall": round(rec_, 5)}


def eval_T2(cand, seeds):
    a = [0, 0]
    for s in seeds:
        ff, fv, R, codes, h = store(s, 1)
        v, _, _ = read(cand, h, ~H.erase(s, 0.9, 0), R, ff, codes, True)
        a[0] += int((v == fv).sum()); a[1] += len(fv)
    acc = a[0] / a[1]
    return acc, {"accuracy": round(acc, 5)}


def eval_T3(cand, seeds):
    err = flg = hit = 0
    for s in seeds:
        ff, fv, R, codes, h = store(s, 0)
        alive = ~H.erase(s, 0.5, 0)
        hd = h * alive.astype(np.int8)
        v1, gap, sup = H.plain_read(hd, R, ff, codes)
        gapflag = gap < cand["c"] * np.sqrt(np.maximum(sup, 1))
        c2 = dict(cand); c2["r6"] = 0
        v2, _, _ = read(c2, h, alive, R, ff, codes, False)
        dis = v2 != v1
        m = int(cand["mode"])
        flag = [gapflag, dis, gapflag & dis, gapflag | dis][m]
        e = v1 != fv
        err += int(e.sum()); flg += int(flag.sum()); hit += int((flag & e).sum())
    rec_ = hit / max(err, 1); prec = hit / max(flg, 1)
    return (prec if rec_ >= 0.95 else prec - 1.0), {"precision": round(prec, 5), "recall": round(rec_, 5)}


EVAL = {"T1": eval_T1, "T2": eval_T2, "T3": eval_T3}


# ------------------------------------------------------------------------------------------------ Root Genome
class Genome:
    def __init__(self, path):
        self.path, self.prev, self.n = path, "0" * 64, 0
        open(path, "w").close()

    def add(self, rec):
        rec = dict(rec); rec["seq"] = self.n; rec["prev"] = self.prev
        line = json.dumps(rec, sort_keys=True)
        self.prev = hashlib.sha256(line.encode()).hexdigest(); self.n += 1
        with open(self.path, "a") as f:
            f.write(line + "\n")
        return rec["seq"]


def verify_chain(path):
    prev = "0" * 64; n = 0
    for line in open(path):
        r = json.loads(line)
        if r["prev"] != prev:
            return False, n
        prev = hashlib.sha256(line.rstrip("\n").encode()).hexdigest(); n += 1
    return True, n


# ------------------------------------------------------------------------------------------------ children
def sample(k, g):
    lo, hi, kind = SPACE[k]
    return int(g.integers(lo, hi + 1)) if kind == "int" else round(float(g.uniform(lo, hi)), 3)


def step(k, v, g, scale):
    lo, hi, kind = SPACE[k]
    if kind == "int":
        return int(np.clip(v + g.choice([-1, 1]), lo, hi))
    return round(float(np.clip(v + g.normal(0, scale * (hi - lo)), lo, hi)), 3)


def propose(child, target, pop, best_other, g):
    keys = TARGET_KEYS[target]
    best = pop[0]["cand"]
    if child == "Tiger":
        c = {k: sample(k, g) for k in keys}
        if g.random() < 0.10:                                     # deliberately outside the safe range
            k = keys[g.integers(len(keys))]; lo, hi, kind = SPACE[k]; c[k] = hi + (1 if kind == "int" else 0.5 * (hi - lo))
        return c, []
    if child == "Lion":
        c = dict(best); k = keys[g.integers(len(keys))]; c[k] = step(k, c[k], g, 0.05); return c, [pop[0]["id"]]
    if child == "Leopard":
        p = pop[g.integers(len(pop))]; c = dict(p["cand"])
        for k in g.choice(keys, int(g.integers(1, 3)), replace=False):
            c[k] = sample(k, g) if g.random() < 0.5 else step(k, c[k], g, 0.15)
        return c, [p["id"]]
    if child == "Dragon":
        if len(pop) < 2:
            return propose("Leopard", target, pop, best_other, g)
        i, j = g.choice(len(pop), 2, replace=False)
        c = {k: (pop[i]["cand"][k] if g.random() < 0.5 else pop[j]["cand"][k]) for k in keys}
        return c, [pop[i]["id"], pop[j]["id"]]
    if child == "WhiteDragon":
        c = dict(best)
        src = best_other[g.integers(len(best_other))]
        for k in keys:
            if k in src["cand"] and k not in ("gate", "mode", "margin", "rounds"):
                c[k] = src["cand"][k]
        return c, [pop[0]["id"], src["id"]]
    raise ValueError(child)


# ------------------------------------------------------------------------------------------------ the run
def run():
    g = np.random.default_rng(2026_11_20)
    genome = Genome(os.path.join(HERE, "ROOT_GENOME.jsonl"))
    out = {"targets": {}, "law0": {"out_of_range_proposed": 0, "refused": 0, "in_range_refused": 0}}
    pops, alloc, succ = {}, {}, {}
    for t in ("T1", "T2", "T3"):                                  # incumbents enter the genome first
        sc, m = EVAL[t](INCUMBENT[t], CAL)
        sid = genome.add({"target": t, "child": "incumbent", "parents": [], "cand": INCUMBENT[t], "law0": True,
                          "cal_score": sc, "cal_metrics": m})
        pops[t] = [{"id": sid, "cand": INCUMBENT[t], "score": sc, "rep": None}]
        alloc[t] = {c: 0 for c in CHILDREN}; succ[t] = {c: [0, 0] for c in CHILDREN}
        out["targets"][t] = {"incumbent_cal": m}
    for i in range(BUDGET):
        for t in ("T1", "T2", "T3"):
            pop = pops[t]
            under = [c for c in CHILDREN if alloc[t][c] < 4]          # Mother: coverage first
            if under:
                child = under[0]
            else:                                                     # Father: Thompson sampling on successes
                draws = {c: g.beta(succ[t][c][0] + 1, succ[t][c][1] + 1) for c in CHILDREN}
                child = max(draws, key=draws.get)
            alloc[t][child] += 1
            if child == "Bear":
                cand_rec = max((p for p in pop if p["rep"] is None), key=lambda p: p["score"], default=pop[0])
                rs, rm = EVAL[t](cand_rec["cand"], REP)
                inc_rs = out["targets"][t].setdefault("incumbent_rep", EVAL[t](INCUMBENT[t], REP)[0])
                cand_rec["rep"] = rs
                ok = rs > inc_rs
                succ[t][child][0 if ok else 1] += 1
                genome.add({"target": t, "child": "Bear", "parents": [cand_rec["id"]], "cand": cand_rec["cand"],
                            "law0": True, "rep_score": rs, "rep_metrics": rm, "replicated": ok})
                continue
            others = [pops[o][0] for o in pops if o != t]
            cand, parents = propose(child, t, pop, others, g)
            ok0 = law0(cand)
            if not ok0:
                out["law0"]["out_of_range_proposed"] += 1; out["law0"]["refused"] += 1
                succ[t][child][1] += 1
                genome.add({"target": t, "child": child, "parents": parents, "cand": cand, "law0": False})
                continue
            sc, m = EVAL[t](cand, CAL)
            better = sc > pop[0]["score"]
            succ[t][child][0 if better else 1] += 1
            sid = genome.add({"target": t, "child": child, "parents": parents, "cand": cand, "law0": True,
                              "cal_score": sc, "cal_metrics": m, "beat_best": better})
            if all(p["cand"] != cand for p in pop):
                pop.append({"id": sid, "cand": cand, "score": sc, "rep": None})
                pop.sort(key=lambda p: -p["score"]); del pop[8:]
        print("round", i, {t: round(pops[t][0]["score"], 4) for t in pops}, flush=True)
    for t in ("T1", "T2", "T3"):                                  # champion challenge on the sealed hold-out
        pop = pops[t]
        reps = [p for p in pop if p["rep"] is not None and p["cand"] != INCUMBENT[t]]
        champ = max(reps, key=lambda p: (p["score"] + p["rep"]) / 2) if reps else \
            next((p for p in pop if p["cand"] != INCUMBENT[t]), None)
        res = out["targets"][t]
        res["alloc"] = alloc[t]; res["successes"] = {c: succ[t][c][0] for c in CHILDREN}
        if champ is None:
            res["challenge"] = None; continue
        hs, hm = EVAL[t](champ["cand"], HOLD)
        ihs, ihm = EVAL[t](INCUMBENT[t], HOLD)
        promoted = hs >= ihs + MARGIN[t]
        genome.add({"target": t, "child": "challenge", "parents": [champ["id"]], "cand": champ["cand"], "law0": True,
                    "hold_score": hs, "hold_metrics": hm, "incumbent_hold": ihm, "promoted": promoted})
        res["challenge"] = {"champion": champ["cand"], "champion_id": champ["id"], "cal": champ["score"],
                            "rep": champ["rep"], "hold": hm, "incumbent_hold": ihm, "promoted": promoted}
    ok, n = verify_chain(genome.path)
    out["genome"] = {"entries": n, "chain_verifies": ok}
    json.dump(out, open(os.path.join(HERE, "RESULTS_ENGINE1.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    run()
