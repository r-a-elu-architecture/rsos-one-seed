"""ENGINE2: SCORE x TOTE engine with grown primitives; transfer of DISAGREE; relations and the information limit.
Predictions: PREREG_ENGINE2.md (sha256 a641004c…71f29, commit 36f950b), sealed before this file."""
import hashlib
import json
import os
import sys

import numpy as np
from scipy.special import ndtr

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "engine")))
import engine1 as E1  # noqa: E402  (stores, hard reader, genome)

H = E1.H
CAL, REP, HOLD = range(800, 804), range(804, 808), range(950, 958)
FIELDS = H.FIELDS
NV = {f: len(H.VALUES[f]) for f in FIELDS}


# ------------------------------------------------------------------------------------------------ soft joint reading
def softmax(x):
    x = x - x.max(1, keepdims=True); e = np.exp(x); return e / e.sum(1, keepdims=True)


def soft_read(h, alive, R, ff, codes, passes=5, sigma_mult=1.0, eps=0.01, temp=1.0, anneal=1.0, prior=None):
    """Every fact keeps probabilities over its candidates; each pass cancels the expected contribution of all
    others and uses their uncertainty. `prior(P)` returns log-prior arrays per field (relations)."""
    hd = (h * alive.astype(np.int8)).astype(np.float32)
    idxs = {fi: np.where(ff == fi)[0] for fi in range(len(FIELDS))}
    P = {}
    for fi, f in enumerate(FIELDS):
        U = hd[None, :] * R[idxs[fi]].astype(np.float32)
        sc = U @ codes[f].T.astype(np.float32)
        P[fi] = softmax(sc / np.sqrt(np.maximum((U != 0).sum(1, keepdims=True), 1)))
    if prior is not None:
        lp = prior(P)
        for fi in P:
            P[fi] = softmax(np.log(P[fi] + 1e-12) + lp[fi])
    hp = (hd > 0)[None, :]
    alive_f = alive.astype(np.float32)[None, :]
    sm = sigma_mult
    for _ in range(int(passes)):
        Eb = np.zeros((len(ff), H.D), np.float32)
        for fi, f in enumerate(FIELDS):
            Eb[idxs[fi]] = R[idxs[fi]].astype(np.float32) * (P[fi].astype(np.float32) @ codes[f].astype(np.float32))
        S_hat = Eb.sum(0); V = (1 - Eb ** 2).sum(0)
        lp = prior(P) if prior is not None else None
        newP = {}
        for fi, f in enumerate(FIELDS):
            ix = idxs[fi]; e = Eb[ix]
            Rh = S_hat[None, :] - e
            sig = np.sqrt(sm ** 2 * np.maximum(V[None, :] - (1 - e ** 2), 0) + 1)
            p_pos = eps + (1 - 2 * eps) * ndtr((Rh + 1.5) / sig)
            p_neg = eps + (1 - 2 * eps) * ndtr((Rh - 0.5) / sig)
            delta = np.where(hp, np.log(p_pos) - np.log(p_neg), np.log1p(-p_pos) - np.log1p(-p_neg)) * alive_f
            score = 0.5 * ((delta * R[ix].astype(np.float32)) @ codes[f].T.astype(np.float32))
            logpost = temp * score + (lp[fi] if lp is not None else 0)
            newP[fi] = softmax(logpost)
        P = newP; sm *= anneal
    v = np.zeros(len(ff), int)
    for fi in P:
        v[idxs[fi]] = P[fi].argmax(1)
    Eb = np.zeros((len(ff), H.D), np.float32)
    for fi, f in enumerate(FIELDS):
        Eb[idxs[fi]] = R[idxs[fi]].astype(np.float32) * (P[fi].astype(np.float32) @ codes[f].astype(np.float32))
    return v, P, Eb


# ------------------------------------------------------------------------------------------------ the engine's space
SPACE = dict(E1.SPACE)
SPACE.update({"rounds": (1, 4, "int"), "tier_decay": (0.3, 1.0, "float"), "soft_recon": (0, 1, "int"),
              "soft": (0, 1, "int"), "temp": (0.25, 2.0, "float"), "anneal": (0.5, 1.0, "float")})
E1.SPACE = SPACE
KEYS = {"T1": ["passes", "sigma_mult", "eps", "c", "r6", "margin", "rounds", "tier_decay", "soft_recon"],
        "T2": ["passes", "sigma_mult", "eps", "gate", "c", "r6", "soft", "temp", "anneal"]}
NEW = {"T1": {"tier_decay": 1.0, "soft_recon": 0}, "T2": {"soft": 0}}
INC = {"T1": dict(E1.INCUMBENT["T1"], tier_decay=1.0, soft_recon=0),
       "T2": dict(E1.INCUMBENT["T2"], soft=0, temp=1.0, anneal=1.0)}
MARGIN = {"T1": 0.10, "T2": 0.02}


def eval_T1(c, seeds):
    on = land = flipped = 0
    for s in seeds:
        ff, fv, R, codes, h = E1.store(s, 1)
        g = np.random.default_rng([s, 202])
        fl = np.zeros(H.D, bool); fl[g.choice(H.D, H.D // 10, replace=False)] = True
        hf = h.copy(); hf[fl] *= -1
        landed = np.zeros(H.D, bool)
        for k in range(int(c["rounds"])):
            if c["soft_recon"]:
                _, _, Eb = soft_read(hf, np.ones(H.D, bool), R, ff, codes, passes=c["passes"],
                                     sigma_mult=c["sigma_mult"], eps=c["eps"])
                S = Eb.sum(0).astype(np.float64)
            else:
                v, w, _ = E1.read(c, hf, np.ones(H.D, bool), R, ff, codes, False)
                S = (w @ H.bindings(R, ff, v, codes).astype(np.int32)).astype(np.float64)
            rec = H.sgn(S)
            need = (rec != hf) & (np.abs(S) >= c["margin"] * (c["tier_decay"] ** k) * S.std()) & ~landed
            hf[need] = rec[need]; landed |= need
        on += int((landed & fl).sum()); land += int(landed.sum()); flipped += int(fl.sum())
    prec = on / land if land else 1.0; rec_ = on / flipped
    return (rec_ if prec >= 0.99 else rec_ - 1.0), {"precision": round(prec, 5), "recall": round(rec_, 5)}


def eval_T2(c, seeds):
    a = [0, 0]
    for s in seeds:
        ff, fv, R, codes, h = E1.store(s, 1)
        alive = ~H.erase(s, 0.9, 0)
        if c["soft"]:
            v, _, _ = soft_read(h, alive, R, ff, codes, passes=c["passes"], sigma_mult=c["sigma_mult"],
                                eps=c["eps"], temp=c["temp"], anneal=c["anneal"])
        else:
            v, _, _ = E1.read(c, h, alive, R, ff, codes, True)
        a[0] += int((v == fv).sum()); a[1] += len(fv)
    return a[0] / a[1], {"accuracy": round(a[0] / a[1], 5)}


EVAL = {"T1": eval_T1, "T2": eval_T2}


def propose(child, t, pop, others, g):
    c, parents = E1.propose(child, t, pop, others, g) if child != "Tiger" else (None, [])
    keys = KEYS[t]
    if child == "Tiger":
        c = {k: E1.sample(k, g) for k in keys}
        if g.random() < 0.10:
            k = keys[g.integers(len(keys))]; lo, hi, kind = SPACE[k]; c[k] = hi + (1 if kind == "int" else 0.5 * (hi - lo))
    for k in keys:                                                     # keep the candidate on this target's keys
        if k not in c:
            c[k] = pop[0]["cand"][k]
    c = {k: c[k] for k in keys}
    if child in ("Tiger", "Dragon") and g.random() < 0.5:              # RSIA: the named causes' new primitives
        if t == "T1":
            c["soft_recon"] = int(g.integers(0, 2)); c["tier_decay"] = round(float(g.uniform(0.3, 0.9)), 3)
            c["rounds"] = int(g.integers(2, 5))
        else:
            c["soft"] = 1
    return c, parents


def run_engine(genome, g):
    out = {}
    explorers = ["Tiger", "Lion", "Leopard", "Dragon", "WhiteDragon"]
    pops = {}
    for t in ("T1", "T2"):
        sc, m = EVAL[t](INC[t], CAL)
        sid = genome.add({"target": t, "child": "incumbent", "parents": [], "cand": INC[t], "law0": True,
                          "cal_score": sc, "cal_metrics": m})
        pops[t] = [{"id": sid, "cand": INC[t], "score": sc, "rep": None}]
        out[t] = {"incumbent_cal": m, "alloc": {c: 0 for c in explorers + ["Bear"]}, "exit": None,
                  "law0_refused": 0, "evals_after_exit": 0}
    succ = {t: {c: [0, 0] for c in explorers} for t in pops}
    E1.TARGET_KEYS.update(KEYS)
    for t in ("T1", "T2"):
        pop = pops[t]; inc = pop[0]["score"]; since = 0; n = 0; bear = 0
        while True:
            if n >= 40:
                out[t]["exit"] = "budget"; break
            if pop[0]["score"] >= inc + MARGIN[t]:
                out[t]["exit"] = "target_met"; break
            if since >= 8:
                out[t]["exit"] = "information_budget"; break
            under = [c for c in explorers if out[t]["alloc"][c] < 3]
            if under:
                child = under[0]
            else:
                d = {c: g.beta(succ[t][c][0] + 1, succ[t][c][1] + 1) for c in explorers}; child = max(d, key=d.get)
            out[t]["alloc"][child] += 1; n += 1
            others = [pops[o][0] for o in pops if o != t] or [pop[0]]
            cand, parents = propose(child, t, pop, others, g)
            if not E1.law0(cand):
                out[t]["law0_refused"] += 1; succ[t][child][1] += 1; since += 1
                genome.add({"target": t, "child": child, "parents": parents, "cand": cand, "law0": False}); continue
            sc, m = EVAL[t](cand, CAL)
            better = sc > pop[0]["score"]
            succ[t][child][0 if better else 1] += 1; since = 0 if better else since + 1
            sid = genome.add({"target": t, "child": child, "parents": parents, "cand": cand, "law0": True,
                              "cal_score": sc, "cal_metrics": m, "beat_best": better})
            if all(p["cand"] != cand for p in pop):
                pop.append({"id": sid, "cand": cand, "score": sc, "rep": None}); pop.sort(key=lambda p: -p["score"]); del pop[8:]
            if n % 6 == 0 and bear < 6:                                  # Bear: its own budget
                cr = next((p for p in pop if p["rep"] is None and p["cand"] != INC[t]), None)
                if cr:
                    rs, rm = EVAL[t](cr["cand"], REP); cr["rep"] = rs; bear += 1; out[t]["alloc"]["Bear"] += 1
                    genome.add({"target": t, "child": "Bear", "parents": [cr["id"]], "cand": cr["cand"], "law0": True,
                                "rep_score": rs, "rep_metrics": rm})
        genome.add({"target": t, "child": "TOTE_exit", "parents": [], "cand": {}, "law0": True, "exit": out[t]["exit"]})
        champ = next((p for p in pop if p["cand"] != INC[t]), None)
        if champ is None:
            out[t]["challenge"] = None; continue
        hs, hm = EVAL[t](champ["cand"], HOLD); ihs, ihm = EVAL[t](INC[t], HOLD)
        promoted = hs >= ihs + MARGIN[t]
        abl = dict(champ["cand"]); abl.update(NEW[t])
        as_, am = EVAL[t](abl, HOLD)
        gain = hs - ihs
        removed = (hs - as_) / gain if gain > 0 else None
        genome.add({"target": t, "child": "challenge", "parents": [champ["id"]], "cand": champ["cand"], "law0": True,
                    "hold": hm, "incumbent_hold": ihm, "ablated_hold": am, "promoted": promoted})
        out[t]["challenge"] = {"champion": champ["cand"], "cal": champ["score"], "rep": champ["rep"], "hold": hm,
                               "incumbent_hold": ihm, "ablated_hold": am, "promoted": promoted,
                               "share_of_gain_removed_by_ablation": None if removed is None else round(removed, 4)}
        print(t, json.dumps(out[t]), flush=True)
    return out


# ------------------------------------------------------------------------------------------------ T4 transfer
DIS = {"passes": 3, "sigma_mult": 1.04, "eps": 0.151, "c": 1.118, "mode": 1, "r6": 0}


def t4():
    res = {}
    for name in ("flips10", "erase30", "erase70"):
        err = flg = hit = 0
        for s in range(960, 968):
            ff, fv, R, codes, h = E1.store(s, 0)
            if name == "flips10":
                g = np.random.default_rng([s, 404]); hh = h.copy()
                hh[g.choice(H.D, H.D // 10, replace=False)] *= -1; alive = np.ones(H.D, bool)
            else:
                hh = h; alive = ~H.erase(s, 0.3 if name == "erase30" else 0.7, 0)
            v1, _, _ = H.plain_read(hh * alive.astype(np.int8), R, ff, codes)
            v2, _, _ = E1.read(DIS, hh, alive, R, ff, codes, False)
            flag = v2 != v1; e = v1 != fv
            err += int(e.sum()); flg += int(flag.sum()); hit += int((flag & e).sum())
        res[name] = {"precision": round(hit / max(flg, 1), 5), "recall": round(hit / max(err, 1), 5), "errors": err}
    return res


# ------------------------------------------------------------------------------------------------ T5 world with relations
P8 = 0.8


def cpt(n_par, n_child, pref):
    T = np.full((n_par, n_child), 0.0)
    for a in range(n_par):
        prefs = pref(a)
        for b in range(n_child):
            T[a, b] = (P8 / len(prefs)) if b in prefs else (1 - P8) / (n_child - len(prefs))
    return T


CPT = {
    "room|owner": cpt(6, 4, lambda a: [a % 4]),
    "on|room": cpt(4, 4, lambda r: [r]),
    "height|on": cpt(4, 50, lambda s: list(range(s * 12, s * 12 + 10))),
    "x|room": cpt(4, 10, lambda r: list(range(min(r * 2, 5), min(r * 2, 5) + 5))),
    "y|room": cpt(4, 10, lambda r: list(range(9 - min(r * 2, 5) - 4, 10 - min(r * 2, 5)))),
}
L = {k: np.log(v) for k, v in CPT.items()}
FI = {f: i for i, f in enumerate(FIELDS)}


def related_scene(seed):
    g = np.random.default_rng([seed, 1000])
    fo, ff, fv, logp = [], [], [], 0.0
    for o in range(50):
        own = int(g.integers(6)); room = int(g.choice(4, p=CPT["room|owner"][own]))
        on = int(g.choice(4, p=CPT["on|room"][room])); hgt = int(g.choice(50, p=CPT["height|on"][on]))
        x = int(g.choice(10, p=CPT["x|room"][room])); y = int(g.choice(10, p=CPT["y|room"][room]))
        vals = {"x": x, "y": y, "height_mm": hgt, "owner": own, "room": room, "on": on}
        logp += np.log(1 / 6) + L["room|owner"][own, room] + L["on|room"][room, on] + L["height|on"][on, hgt] \
            + L["x|room"][room, x] + L["y|room"][room, y]
        for f in FIELDS:
            fo.append(o); ff.append(FI[f]); fv.append(vals[f])
    return np.array(fo), np.array(ff), np.array(fv), -logp / np.log(2)


def network_prior(P):
    """Mean-field log-prior per field, given the other fields' current probabilities (objects in order)."""
    Po, Pr, Ps, Ph, Px, Py = (P[FI[f]] for f in ("owner", "room", "on", "height_mm", "x", "y"))
    lp = {}
    lp[FI["owner"]] = Pr @ L["room|owner"].T
    lp[FI["room"]] = Po @ L["room|owner"] + Ps @ L["on|room"].T + Px @ L["x|room"].T + Py @ L["y|room"].T
    lp[FI["on"]] = Pr @ L["on|room"] + Ph @ L["height|on"].T
    lp[FI["height_mm"]] = Ps @ L["height|on"]
    lp[FI["x"]] = Pr @ L["x|room"]
    lp[FI["y"]] = Pr @ L["y|room"]
    return lp


def map_guess():
    own = 0; room = int(CPT["room|owner"][own].argmax()); on = int(CPT["on|room"][room].argmax())
    return {"x": int(CPT["x|room"][room].argmax()), "y": int(CPT["y|room"][room].argmax()),
            "height_mm": int(CPT["height|on"][on].argmax()), "owner": own, "room": room, "on": on}


def t5():
    res = {}
    arm = dict(codes="rand", r6=True, heal=False, gate=False)
    mg = map_guess()
    R5c = {"passes": 5, "sigma_mult": 1.0, "eps": 0.01, "c": 2.0, "r6": 0, "gate": 1.0}
    for loss in (0.85, 0.9, 0.95, 0.98):
        acc = {k: [0, 0] for k in ("H", "S", "SR", "CC", "CU")}
        for s in range(1000, 1016):
            fo, ff, fv, bits = related_scene(s)
            R, codes, h = H.holo_store(arm, fo, ff, fv)
            alive = ~H.erase(s, loss, 0)
            vH, _, _ = E1.read(R5c, h, alive, R, ff, codes, False)
            vS, _, _ = soft_read(h, alive, R, ff, codes)
            vSR, _, _ = soft_read(h, alive, R, ff, codes, prior=network_prior)
            surv = int(alive.sum())
            guess = np.array([mg[FIELDS[i]] for i in ff])
            vCC = fv if surv >= bits + 20 else guess
            vCU = fv if surv >= 1050 + 20 else guess
            for k, v in (("H", vH), ("S", vS), ("SR", vSR), ("CC", vCC), ("CU", vCU)):
                acc[k][0] += int((v == fv).sum()); acc[k][1] += len(fv)
            res.setdefault("compressed_bits", []).append(round(bits, 1))
        res[str(loss)] = {k: round(a / b, 5) for k, (a, b) in acc.items()}
        print("T5", loss, res[str(loss)], flush=True)
    res["compressed_bits_mean"] = round(float(np.mean(res.pop("compressed_bits"))), 1)
    return res


def main():
    g = np.random.default_rng(20261121)
    genome = E1.Genome(os.path.join(HERE, "ROOT_GENOME_2.jsonl"))
    out = {"T4": t4()}; print("T4", out["T4"], flush=True)
    out["T5"] = t5()
    out["engine"] = run_engine(genome, g)
    ok, n = E1.verify_chain(genome.path)
    out["genome"] = {"entries": n, "chain_verifies": ok}
    json.dump(out, open(os.path.join(HERE, "RESULTS_ENGINE2.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
