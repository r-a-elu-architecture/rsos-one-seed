"""rsos_engine: the seed's self-growing engine as one library (genome, six children, Father, Mother, SCORE x TOTE,
Law 0). Used by RSOS (research/) and Cosmology (RSOS_ENGINE/). Apache-2.0, part of RSOS-Language.

A host supplies: the primitive space, an incumbent, a score function on calibration, a Law 0 predicate, optional
replication on a second calibration split, the named causes (SCORE's C) as primitive settings, and a target test.
"""
import hashlib
import json

import numpy as np


class Genome:
    """Append-only, hash-chained Omega Root Genome."""

    def __init__(self, path):
        self.path, self.prev, self.n = path, "0" * 64, 0
        open(path, "w").close()

    def add(self, rec):
        rec = dict(rec, seq=self.n, prev=self.prev)
        line = json.dumps(rec, sort_keys=True, default=str)
        self.prev = hashlib.sha256(line.encode()).hexdigest(); self.n += 1
        with open(self.path, "a") as f:
            f.write(line + "\n")
        return rec["seq"]

    @staticmethod
    def verify(path):
        prev = "0" * 64
        for line in open(path):
            if json.loads(line)["prev"] != prev:
                return False
            prev = hashlib.sha256(line.rstrip("\n").encode()).hexdigest()
        return True


class Space:
    def __init__(self, spec):
        self.spec = spec                                   # name -> (lo, hi, "int" | "float")

    def sample(self, k, g):
        lo, hi, kind = self.spec[k]
        return int(g.integers(lo, hi + 1)) if kind == "int" else round(float(g.uniform(lo, hi)), 3)

    def fresh(self, g):
        return {k: self.sample(k, g) for k in self.spec}

    def in_range(self, c):
        return all(self.spec[k][0] <= v <= self.spec[k][1] for k, v in c.items() if k in self.spec)


EXPLORERS = ("Tiger", "Lion", "Leopard", "Dragon", "WhiteDragon")


def propose(child, space, pop, causes, g):
    best = pop[0]["cand"]
    if child == "Tiger":
        c = space.fresh(g)
    elif child == "Lion":
        c = dict(best); k = list(space.spec)[g.integers(len(space.spec))]; c[k] = space.sample(k, g)
    elif child == "Leopard":
        c = dict(pop[g.integers(len(pop))]["cand"])
        for k in g.choice(list(space.spec), min(2, len(space.spec)), replace=False):
            c[k] = space.sample(k, g)
    elif child == "Dragon":
        i, j = g.choice(len(pop), 2, replace=len(pop) < 2)
        c = {k: (pop[i]["cand"][k] if g.random() < 0.5 else pop[j]["cand"][k]) for k in space.spec}
    else:                                                  # White Dragon: carry what the others found
        c = dict(best)
        for k, v in pop[-1]["cand"].items():
            if g.random() < 0.3:
                c[k] = v
    if child in ("Tiger", "Dragon") and causes and g.random() < 0.5:     # RSIA: SCORE's named causes
        for setting in causes:
            c.update(setting)
    return c


def run(space, incumbent, score, law0, target_met, genome, g, causes=(), replicate=None,
        max_evals=40, patience=8, bear_budget=6, coverage=3):
    """SCORE x TOTE: test -> operate (children) -> test -> exit. Returns the champion and the run record."""
    s0 = score(incumbent)
    genome.add({"child": "incumbent", "cand": incumbent, "score": s0})
    pop = [{"cand": incumbent, "score": s0, "rep": None}]
    alloc = {c: 0 for c in EXPLORERS + ("Bear",)}; succ = {c: [0, 0] for c in EXPLORERS}
    n = since = refused = bear = 0; exit_reason = None
    while True:
        if n >= max_evals:
            exit_reason = "budget"; break
        if since >= patience:
            exit_reason = "information_budget"; break
        if pop[0]["cand"] != incumbent and target_met(pop[0]["cand"]):
            exit_reason = "target_met"; break
        under = [c for c in EXPLORERS if alloc[c] < coverage]                 # Mother: coverage
        child = under[0] if under else max(EXPLORERS, key=lambda c: g.beta(succ[c][0] + 1, succ[c][1] + 1))  # Father
        alloc[child] += 1; n += 1
        cand = propose(child, space, pop, causes, g)
        if not space.in_range(cand) or not law0(cand):                        # Law 0 before evaluation
            refused += 1; succ[child][1] += 1; since += 1
            genome.add({"child": child, "cand": cand, "law0": "refused"}); continue
        sc = score(cand); better = sc > pop[0]["score"]
        succ[child][0 if better else 1] += 1; since = 0 if better else since + 1
        genome.add({"child": child, "cand": cand, "score": sc, "beat_best": better})
        if all(p["cand"] != cand for p in pop):
            pop.append({"cand": cand, "score": sc, "rep": None}); pop.sort(key=lambda p: -p["score"]); del pop[8:]
        if replicate and n % 6 == 0 and bear < bear_budget:                   # Bear: its own budget
            top = next((p for p in pop if p["rep"] is None and p["cand"] != incumbent), None)
            if top:
                top["rep"] = replicate(top["cand"]); bear += 1; alloc["Bear"] += 1
                genome.add({"child": "Bear", "cand": top["cand"], "rep": top["rep"]})
    genome.add({"child": "TOTE_exit", "exit": exit_reason})
    champ = next((p for p in pop if p["cand"] != incumbent), pop[0])["cand"]
    return champ, {"exit": exit_reason, "evaluations": n, "law0_refused": refused, "alloc": alloc}
