"""HOLO4: the White Dragon heals the quark of HOLO3 (owner 12:42).
Operators (owner's definitions, register): U90 White Dragon find/show/heal only the differing chunks; U115 library
of all knowledge (past/present/future); U101 golden light, best paths by shared relations; U102 green particle lands
on the shared relation, becomes part of the sphere, opens its library; U103 deficit bounds the landing; U104 tiger
(closest path) then lion (boldest path); new 12:42: the particle clone goes to every place in the structure where it
heals, and changes the DNA (the quark's seed: weights and order) for the whole.
Phases: heal  -> on training seeds 400-407 only; writes DNA_healed.json
        test  -> on fresh seeds 500-515 only; reads the sealed DNA
Usage: python holo4.py heal | python holo4.py test"""
import sys, json, itertools, math, hashlib
import numpy as np

Q, M = 4, 8
DNA0 = {"order": "VAKOG", "w_wait": 0.10, "V_est": 0.30, "V_q": 0.05, "A_io": 0.50, "A_rel": 0.30, "A_pre": -0.20,
        "K_rate": 0.50, "O_dep": 0.40, "O_diff": 0.20, "G_rel": 0.30}
SUB = {"V": ["V_est", "V_q"], "A": ["A_io", "A_rel", "A_pre"], "K": ["K_rate"], "O": ["O_dep", "O_diff"], "G": ["G_rel"]}

def make_jobs(d, seed):
    r = np.random.default_rng(seed); n = 10 * d; jobs = []
    for j in range(n):
        k = int(r.integers(3, 7))
        bursts = [int(r.geometric(1 / 6)) if b % 2 == 0 else int(r.geometric(1 / 8)) for b in range(2 * k - 1)]
        parent = int(r.integers(0, j)) if (j > 0 and r.random() < 0.1 * d) else -1
        jobs.append({"arr": int(r.integers(0, 40 * d)), "bursts": bursts, "parent": parent})
    return jobs

class Proc:
    def __init__(s, i, j):
        s.id, s.arr, s.b, s.bi, s.parent = i, j["arr"], j["bursts"], 0, j["parent"]; s.left = s.b[0]
        s.state = "New"; s.est = 6.0; s.prev_est = 6.0; s.wait = 0; s.served = 0; s.kst = 0.0; s.event = "none"
        s.done_t = None; s.service = sum(j["bursts"]); s.slot = False

def score(p, procs, dna, coupled, qlen):
    u0 = p.wait * dna["w_wait"]
    dep = sum(1 for o in procs if o.parent == p.id and o.state != "Terminated")
    def V(u): return u - dna["V_est"] * p.est / 10.0 + dna["V_q"] * qlen / 10.0
    def A(u): return u + {"io": dna["A_io"], "release": dna["A_rel"], "preempt": dna["A_pre"]}.get(p.event, 0.0)
    def K(u): p.kst = (1 - dna["K_rate"]) * p.kst + dna["K_rate"] * u; return p.kst
    def O(u): return u + dna["O_dep"] * dep - dna["O_diff"] * (p.est - p.prev_est) / 6.0
    def G(u): return u * (1 - dna["G_rel"] * math.tanh(p.served / (p.wait + 1.0)))
    f = {"V": V, "A": A, "K": K, "O": O, "G": G}
    if coupled:
        u = u0
        for m in dna["order"]: u = f[m](u)
        return u
    s = u0
    for m in dna["order"]: s += f[m](u0) - u0
    return s

def simulate(d, seed, policy, dna=None, coupled=True, horizon=4000):
    procs = [Proc(i, j) for i, j in enumerate(make_jobs(d, seed))]
    run, run_q, io_q, io_cur, t = None, 0, [], None, 0
    while t < horizon and any(p.state != "Terminated" for p in procs):
        for p in procs:
            if p.state == "New" and t >= p.arr and (p.parent < 0 or procs[p.parent].state == "Terminated"):
                p.state = "SuspReady"; p.event = "release" if p.parent >= 0 else "none"
        resident = [p for p in procs if p.slot and p.state != "Terminated"]
        cand = [p for p in procs if p.state == "SuspReady" and not p.slot]
        while len(resident) < M and cand:
            if policy == "quark":
                ql = len(cand); cand.sort(key=lambda p: -score(p, procs, dna, coupled, ql))
            elif policy == "hist": cand.sort(key=lambda p: p.est)
            else: cand.sort(key=lambda p: p.arr)
            p = cand.pop(0); p.slot = True; p.state = "Ready"; resident.append(p)
        if io_cur is None and io_q: io_cur = io_q.pop(0)
        if io_cur is not None:
            io_cur.left -= 1
            if io_cur.left <= 0:
                io_cur.bi += 1; io_cur.left = io_cur.b[io_cur.bi]; io_cur.state = "Ready"; io_cur.event = "io"; io_cur = None
        if run is not None and run_q >= Q: run.state = "Ready"; run.event = "preempt"; run = None
        if run is None:
            ready = [p for p in procs if p.state == "Ready"]
            if ready:
                if policy == "quark":
                    ql = len(ready); run = max(ready, key=lambda p: score(p, procs, dna, coupled, ql))
                elif policy == "hist": run = min(ready, key=lambda p: (p.est, p.arr))
                else: run = min(ready, key=lambda p: (-p.wait, p.arr))
                run.state = "Running"; run_q = 0; run.wait = 0
        for p in procs:
            if p.state == "Ready": p.wait += 1
        if run is not None:
            run.left -= 1; run.served += 1; run_q += 1
            if run.left <= 0:
                burst = run.b[run.bi]; run.prev_est = run.est; run.est = 0.5 * run.est + 0.5 * burst; run.bi += 1
                if run.bi >= len(run.b): run.state = "Terminated"; run.done_t = t; run.slot = False
                else: run.left = run.b[run.bi]; run.state = "Waiting"; io_q.append(run)
                run = None
        t += 1
    return -float(np.mean([((p.done_t if p.done_t is not None else horizon) - p.arr + 1) / p.service for p in procs]))

DENS = [1, 2, 3, 4, 5]
def baselines(seeds):
    return {(d, s): max(simulate(d, s, "rr"), simulate(d, s, "hist")) for d in DENS for s in seeds}
def advantage(dna, seeds, base, coupled=True):
    return float(np.mean([simulate(d, s, "quark", dna, coupled) - base[(d, s)] for d in DENS for s in seeds]))

if sys.argv[1] == "heal":
    TR = list(range(400, 408)); base = baselines(TR); log = []
    dna = dict(DNA0); cur = advantage(dna, TR, base); log.append(("start", cur))
    # 1. White Dragon FIND (U90): which subnode chunks differ from what the host needs? remove each; if G rises
    #    or stays, that chunk is a deficit (it does not carry its part).
    deficit = []
    for sn, keys in SUB.items():
        t = dict(dna)
        for k in keys: t[k] = 0.0
        a = advantage(t, TR, base); log.append(("find_" + sn, a))
        if a >= cur: deficit.append(sn)
    if not deficit: deficit = list(SUB)
    # also the trunk signal (waiting, the round-robin principle from the library of past schedulers) is a chunk
    # 2. LIBRARY + GOLDEN LIGHT (U115, U101): candidate particles for each deficit key = the same relation at other
    #    strengths and signs (equivalents across the library: none, half, same, double, fourfold, inverted)
    LIB = [0.0, 0.5, 1.0, 2.0, 4.0, -1.0]
    # 3. GREEN PARTICLE LANDING (U102, U103, U104): land only on deficit chunks; tiger first (closest path:
    #    one key at a time), then lion (boldest: the best order for the whole quark)
    keys = [k for sn in deficit for k in SUB[sn]] + ["w_wait"]
    for sweep in range(2):
        for k in keys:
            best_v, best_a = dna[k], cur
            for m in LIB:
                v = (DNA0[k] if DNA0[k] != 0 else 0.1) * m
                if v == dna[k]: continue
                t = dict(dna); t[k] = v; a = advantage(t, TR, base)
                if a > best_a + 1e-9: best_v, best_a = v, a
            if best_a > cur: dna[k] = best_v; cur = best_a; log.append(("land_" + k, cur))
    orders = ["".join(p) for p in itertools.permutations("VAKOG")]
    ores = {o: advantage(dict(dna, order=o), TR, base) for o in orders}
    o_best = max(ores, key=ores.get)
    if ores[o_best] > cur: dna["order"] = o_best; cur = ores[o_best]; log.append(("lion_order_" + o_best, cur))
    # 4. CLONE + DNA (12:42): the healed seed is written once and cloned to every process, every state, every density
    out = {"DNA_healed": dna, "DNA_start": DNA0, "deficit_found": deficit, "train_adv_start": log[0][1],
           "train_adv_healed": cur, "log": log, "keys_changed": [k for k in DNA0 if dna[k] != DNA0[k]]}
    json.dump(out, open("DNA_healed.json", "w"), indent=1); print(json.dumps(out, indent=1))

if sys.argv[1] == "test":
    H = json.load(open("DNA_healed.json")); dna = H["DNA_healed"]
    from scipy.stats import binomtest, spearmanr
    TS = list(range(500, 516)); R = {"dna_sha256": hashlib.sha256(open("DNA_healed.json", "rb").read()).hexdigest()}
    adv = {}; advu = {}; adv0 = {}
    for d in DENS:
        rows = []
        for s in TS:
            b = max(simulate(d, s, "rr"), simulate(d, s, "hist"))
            rows.append((simulate(d, s, "quark", dna, True) - b, simulate(d, s, "quark", dna, False) - b,
                         simulate(d, s, "quark", DNA0, True) - b))
        rows = np.array(rows); adv[d], advu[d], adv0[d] = rows[:, 0], rows[:, 1], rows[:, 2]
        R[f"d{d}"] = {"adv_healed": float(rows[:, 0].mean()), "adv_healed_uncoupled": float(rows[:, 1].mean()),
                      "adv_before_heal": float(rows[:, 2].mean()), "healed_wins_vs_best_baseline": int(np.sum(rows[:, 0] > 0))}
    def sp(x): w = int(np.sum(x > 0)); return {"wins": w, "of": len(x), "p": float(binomtest(w, len(x), 0.5, alternative="greater").pvalue)}
    R["W1_healed_beats_best_baseline_d5"] = sp(adv[5])
    rho, p = spearmanr([d for d in DENS for _ in TS], [v for d in DENS for v in adv[d]])
    R["W2_advantage_grows_with_density"] = {"rho": float(rho), "p": float(p)}
    R["W3_coupled_beats_uncoupled_d5"] = sp(adv[5] - advu[5])
    R["W4_healed_beats_unhealed_all_densities"] = sp(np.concatenate([adv[d] - adv0[d] for d in DENS]))
    json.dump(R, open("RESULTS_HOLO4.json", "w"), indent=1); print(json.dumps(R, indent=1))
