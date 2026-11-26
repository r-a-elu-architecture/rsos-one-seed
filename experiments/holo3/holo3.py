"""HOLO3: VAKOG quarks on an operating-system process lifecycle; "hot" = the space of relations (owner 12:31).
States: New, Ready, Running, Waiting (I/O), Terminated, Suspended-Ready, Suspended-Blocked (memory slots M).
Relation density d = 1..5 raises processes, dependencies (a process waits for its parent to terminate) and
shared-I/O contention. Each process is a quark; its five subnodes (owner 11:50, computer reading) set its priority:
  V sees: its own remaining-work estimate against the queue
  A hears: the last event (I/O done, parent released, timer preempt) and selects the protocol (boost/keep/demote)
  K the policy applied in structural order (a graded, persistent priority ramp)
  O smells what is different from before: the trace of every process it touched (dependents waiting on it)
    and the change in its burst estimate
  G relief: well fed when served; tempers the chain
Order of letters = the program (U157). Coupled: the signal passes through the chain. Uncoupled: the same five parts,
each from the raw signal, summed. Baselines: round-robin; history (exponential burst estimate, shortest first).
G-endpoint = -(mean slowdown) = -(mean turnaround / own service time); higher is better.
Usage: python holo3.py <out.json> [--quick]"""
import sys, json, itertools, math
import numpy as np

Q, M = 4, 8
def make_jobs(d, seed):
    r = np.random.default_rng(seed); n = 10 * d; jobs = []
    for j in range(n):
        k = int(r.integers(3, 7))
        bursts = [int(r.geometric(1 / 6)) if b % 2 == 0 else int(r.geometric(1 / 8)) for b in range(2 * k - 1)]
        parent = int(r.integers(0, j)) if (j > 0 and r.random() < 0.1 * d) else -1
        jobs.append({"arr": int(r.integers(0, 40 * d)), "bursts": bursts, "parent": parent})
    return jobs

class Proc:
    __slots__ = ("id", "arr", "b", "bi", "left", "parent", "state", "est", "prev_est", "wait", "served", "kst",
                 "event", "done_t", "service", "kick", "rec", "slot")
    def __init__(s, i, j):
        s.id, s.arr, s.b, s.bi, s.parent = i, j["arr"], j["bursts"], 0, j["parent"]; s.left = s.b[0]
        s.state = "New"; s.est = 6.0; s.prev_est = 6.0; s.wait = 0; s.served = 0; s.kst = 0.0; s.event = "none"
        s.done_t = None; s.service = sum(j["bursts"]); s.kick = 0.0; s.rec = []; s.slot = False

def quark_score(p, procs, order, coupled, qlen):
    u0 = p.wait / 10.0
    dependents = sum(1 for o in procs if o.parent == p.id and o.state != "Terminated")
    def V(u): return u - 0.3 * p.est / 10.0 + 0.05 * qlen / 10.0
    def A(u): return u + {"io": 0.5, "release": 0.3, "preempt": -0.2}.get(p.event, 0.0)
    def K(u): p.kst = 0.5 * p.kst + 0.5 * u; return p.kst
    def O(u): return u + 0.4 * dependents - 0.2 * (p.est - p.prev_est) / 6.0 + p.kick
    def G(u): return u * (1 - 0.3 * math.tanh(p.served / (p.wait + 1.0)))
    f = {"V": V, "A": A, "K": K, "O": O, "G": G}; out = {}
    if coupled:
        u = u0
        for m in order: u = f[m](u); out[m] = u
        score = u
    else:
        score = u0
        for m in order: v = f[m](u0); out[m] = v; score += v - u0
    p.rec.append([out[m] for m in "VAKOG"])
    return score

def simulate(d, seed, policy, order="VAKOG", coupled=True, kick=None, horizon=4000):
    procs = [Proc(i, j) for i, j in enumerate(make_jobs(d, seed))]
    run, run_q, io_q, io_cur, t = None, 0, [], None, 0
    while t < horizon and any(p.state != "Terminated" for p in procs):
        if kick and t == kick[0]: procs[kick[1]].kick += 1.0
        for p in procs:                                   # New -> admitted when parent done
            if p.state == "New" and t >= p.arr and (p.parent < 0 or procs[p.parent].state == "Terminated"):
                p.state = "SuspReady"; p.event = "release" if p.parent >= 0 else "none"
        resident = [p for p in procs if p.slot and p.state != "Terminated"]
        cand = [p for p in procs if p.state == "SuspReady" and not p.slot]
        while len(resident) < M and cand:                 # admission: suspended -> ready (memory slot)
            if policy == "quark":
                ql = len(cand); cand.sort(key=lambda p: -quark_score(p, procs, order, coupled, ql))
            elif policy == "hist": cand.sort(key=lambda p: p.est)
            else: cand.sort(key=lambda p: p.arr)
            p = cand.pop(0); p.slot = True; p.state = "Ready"; resident.append(p)
        if io_cur is None and io_q:                       # shared I/O device, FIFO (contention)
            io_cur = io_q.pop(0)
        if io_cur is not None:
            io_cur.left -= 1
            if io_cur.left <= 0:
                io_cur.bi += 1; io_cur.left = io_cur.b[io_cur.bi]; io_cur.state = "Ready"; io_cur.event = "io"; io_cur = None
        if run is not None and (run_q >= Q):              # timer preempt
            run.state = "Ready"; run.event = "preempt"; run = None
        if run is None:
            ready = [p for p in procs if p.state == "Ready"]
            if ready:
                if policy == "quark":
                    ql = len(ready); run = max(ready, key=lambda p: quark_score(p, procs, order, coupled, ql))
                elif policy == "hist": run = min(ready, key=lambda p: (p.est, p.arr))
                else: run = min(ready, key=lambda p: (p.wait * -1, p.arr))
                run.state = "Running"; run_q = 0; run.wait = 0
        for p in procs:
            if p.state == "Ready": p.wait += 1
        if run is not None:
            run.left -= 1; run.served += 1; run_q += 1
            if run.left <= 0:
                burst = run.b[run.bi]; run.prev_est = run.est; run.est = 0.5 * run.est + 0.5 * burst
                run.bi += 1
                if run.bi >= len(run.b):
                    run.state = "Terminated"; run.done_t = t; run.slot = False
                else:
                    run.left = run.b[run.bi]; run.state = "Waiting"; io_q.append(run)
                run = None
        t += 1
    sl = [((p.done_t if p.done_t is not None else horizon) - p.arr + 1) / p.service for p in procs]
    return -float(np.mean(sl)), procs

ORDERS = ["".join(p) for p in itertools.permutations("VAKOG")]
QUICK = "--quick" in sys.argv
DENS = [1, 2, 3, 4, 5]; SEEDS = list(range(300, 303 if QUICK else 308)); ORD = ORDERS[:6] if QUICK else ORDERS
R = {"densities": DENS, "seeds": SEEDS, "orders": len(ORD)}
from scipy.stats import spearmanr, binomtest
tab = {}
for d in DENS:
    rr = np.array([simulate(d, s, "rr")[0] for s in SEEDS]); hi = np.array([simulate(d, s, "hist")[0] for s in SEEDS])
    qc = np.array([[simulate(d, s, "quark", o, True)[0] for s in SEEDS] for o in ORD])
    qu = np.array([simulate(d, s, "quark", "VAKOG", False)[0] for s in SEEDS])
    med_o = int(np.argsort(qc.mean(1))[len(ORD) // 2]); best_o = int(qc.mean(1).argmax())
    base = np.maximum(rr, hi)
    tab[d] = {"rr": rr, "hist": hi, "qc_med": qc[med_o], "qc_all_mean": qc.mean(0), "qu": qu, "base": base,
              "order_means": qc.mean(1)}
    R[f"d{d}"] = {"G_rr": float(rr.mean()), "G_hist": float(hi.mean()), "G_quark_median_order": float(qc[med_o].mean()),
                  "median_order": ORD[med_o], "G_quark_best_order": float(qc[best_o].mean()), "best_order": ORD[best_o],
                  "G_quark_uncoupled": float(qu.mean()), "adv_median_vs_best_baseline": float((qc[med_o] - base).mean()),
                  "order_spread": float(qc.mean(1).max() - qc.mean(1).min())}
# P2: advantage grows with relation density
xs = [d for d in DENS for _ in SEEDS]; ys = [v for d in DENS for v in (tab[d]["qc_med"] - tab[d]["base"])]
rho, p = spearmanr(xs, ys)
R["P2"] = {"adv_d1": R["d1"]["adv_median_vs_best_baseline"], "adv_d5": R["d5"]["adv_median_vs_best_baseline"],
           "spearman_rho": float(rho), "p": float(p),
           "pass": bool(R["d5"]["adv_median_vs_best_baseline"] > R["d1"]["adv_median_vs_best_baseline"] and rho > 0 and p < 0.05)}
# P2b: coupled vs uncoupled at d=5 (same parts, chain only)
w = int(np.sum(tab[5]["qc_med"] > tab[5]["qu"]))
R["P2b_coupled_vs_uncoupled_d5"] = {"wins": w, "of": len(SEEDS),
    "p": float(binomtest(w, len(SEEDS), 0.5, alternative="greater").pvalue), "mean_diff": float((tab[5]["qc_med"] - tab[5]["qu"]).mean())}
# P3: under every order, a trigger on O of one process (t=60) reaches all five of its subnodes and other processes (d=5)
reach, others = [], []
for o in ORD:
    _, b = simulate(5, SEEDS[0], "quark", o, True); _, pt = simulate(5, SEEDS[0], "quark", o, True, kick=(60, 3))
    rb, rp = np.array(b[3].rec), np.array(pt[3].rec); n = min(len(rb), len(rp))
    diff = np.abs(rb[:n] - rp[:n]).max(0) if n else np.zeros(5)
    reach.append(bool(np.all(diff > 0)) or len(rb) != len(rp) and bool(np.all(diff > 0)))
    others.append(int(sum(1 for x, y in zip(b, pt) if x.id != 3 and x.done_t != y.done_t)))
R["P3"] = {"orders_all_five_changed": int(sum(reach)), "of": len(ORD),
           "other_processes_changed_median": float(np.median(others)), "range": [int(min(others)), int(max(others))]}
# P1: same structure at two levels: 5x5 correlation among subnodes at process level vs system level
_, ps = simulate(5, SEEDS[0], "quark", "VAKOG", True)
P = np.vstack([np.array(p.rec) for p in ps if len(p.rec) > 3])
# system level: the five subnodes read from system aggregates per dispatch (queue, events, switch, change, relief)
S = []
for p in ps:
    for i, r in enumerate(p.rec): S.append(r)
Cp = np.corrcoef(P.T)
blocks = np.array_split(P, 50); Sys = np.array([b.mean(0) for b in blocks if len(b)])   # system = aggregate per window
Cs = np.corrcoef(Sys.T); iu = np.triu_indices(5, 1)
obs = spearmanr(Cp[iu], Cs[iu])[0]; rng = np.random.default_rng(1); null = []
for _ in range(2000):
    pm = rng.permutation(5); null.append(spearmanr(Cp[iu], Cs[pm][:, pm][iu])[0])
R["P1"] = {"spearman_levels": float(obs), "null_95": float(np.nanpercentile(null, 95)),
           "p": float((np.sum(np.array(null) >= obs) + 1) / 2001),
           "note": "system level = the same subnodes aggregated per time window (disclosed: shares definitions)"}
json.dump(R, open(sys.argv[1], "w"), indent=1); print(json.dumps(R, indent=1))
