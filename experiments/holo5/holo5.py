"""HOLO5: the White Dragon as the owner defined it (21 Nov 2026, 13:00): register U159-U164.
  U159 golden light inside every level  -> every dispatch decision of every process at every tick is lit (full trace)
  U160 letter address                   -> each decision gets a unique address: (ready count, longest wait, I/O queue,
                                           which lenses agree) = the state and VAKOG at that moment
  U163 past / present / future          -> the world is frozen at the decision (present), its trace is the past, and
                                           every possible choice is run forward from a copy (the futures)
  U161 green particle landing           -> a particle lands on an address only where a different choice heals the
                                           whole: every channel no worse and the whole better (U164 turquoise target)
  U162 green tube sphere                -> landings are connected by shared address parts; an unseen exact address is
                                           reached through its tube (the same address with one part dropped)
  clone (12:42)                         -> the landed rules are carried to unseen worlds, at the same addresses only;
                                           everywhere else the unhealed quark (HOLO3 DNA0) runs unchanged (trunk intact)
Phases: heal -> training seeds 400-463 (64 worlds) only; writes LANDINGS.json
        test -> fresh seeds 500-515 only (same as HOLO4, for a direct delta); reads the sealed LANDINGS.json
Usage: python holo5.py check | heal | test"""
import sys, json, math, copy, hashlib, itertools
from collections import defaultdict
import numpy as np

HERE = __file__.rsplit("/", 1)[0] if "/" in __file__ else "."
Q, M = 4, 8
DNA0 = {"order": "VAKOG", "w_wait": 0.10, "V_est": 0.30, "V_q": 0.05, "A_io": 0.50, "A_rel": 0.30, "A_pre": -0.20,
        "K_rate": 0.50, "O_dep": 0.40, "O_diff": 0.20, "G_rel": 0.30}
DENS = [1, 2, 3, 4, 5]
LENSES = ["quark", "rr", "hist", "rel"]   # quark = unhealed DNA0; rr = longest wait; hist = shortest estimate;
                                          # rel = most live dependants (the relation lens)

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

def score(p, procs, dna, coupled, qlen):          # identical to HOLO3/HOLO4
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

def bucket(x, edges):
    for i, e in enumerate(edges):
        if x <= e: return i
    return len(edges)

class World:
    """The same host as HOLO3/HOLO4, written so that it can be frozen and copied at any decision."""
    def __init__(s, d, seed, policy, dna=None, coupled=True, horizon=4000, rules=None):
        s.procs = [Proc(i, j) for i, j in enumerate(make_jobs(d, seed))]
        s.run, s.run_q, s.io_q, s.io_cur, s.t = None, 0, [], None, 0
        s.policy, s.dna, s.coupled, s.horizon, s.rules = policy, dna, coupled, horizon, rules
        s.io_idle = 0; s.landed_used = 0; s.decisions = 0

    def alive(s): return s.t < s.horizon and any(p.state != "Terminated" for p in s.procs)

    def lens_pick(s, lens, ready):
        if lens == "quark":
            ql = len(ready); return max(ready, key=lambda p: score(p, s.procs, s.dna or DNA0, s.coupled, ql))
        if lens == "hist": return min(ready, key=lambda p: (p.est, p.arr))
        if lens == "rr": return min(ready, key=lambda p: (-p.wait, p.arr))
        if lens == "rel":
            dep = lambda p: sum(1 for o in s.procs if o.parent == p.id and o.state != "Terminated")
            return max(ready, key=lambda p: (dep(p), p.wait, -p.arr))

    def address(s, ready, picks):
        mw = max(p.wait for p in ready)
        agree = tuple(int(picks[a].id == picks[b].id) for a, b in [("quark", "rr"), ("quark", "hist"), ("quark", "rel")])
        return (bucket(len(ready), [1, 3, 6]), bucket(mw, [4, 14, 39]), bucket(len(s.io_q), [0, 2]), agree)

    def choose(s, ready):
        # returns the process to run; for the policies of HOLO4 the arithmetic is identical
        if s.policy in ("quark", "hist", "rr"):
            if s.policy == "quark":
                # NB: score() mutates p.kst (the K channel); lens_pick("quark") calls it exactly once per ready proc,
                # as HOLO4 did, so the trace is identical
                return s.lens_pick("quark", ready)
            return s.lens_pick(s.policy, ready)
        if s.policy == "landed":
            # the quark is always evaluated first (its K state keeps flowing, identical to the unhealed run)
            q = s.lens_pick("quark", ready)
            if len(ready) < 2: return q
            picks = {"quark": q, "rr": s.lens_pick("rr", ready), "hist": s.lens_pick("hist", ready),
                     "rel": s.lens_pick("rel", ready)}
            if len({p.id for p in picks.values()}) == 1: return q
            lens = lookup(s.rules, s.address(ready, picks))
            if lens and lens != "quark": s.landed_used += 1; return picks[lens]
            return q

    def pre(s):
        """Everything in one tick before the dispatch. Returns the ready set if a dispatch is due (the letter)."""
        procs, t = s.procs, s.t
        for p in procs:
            if p.state == "New" and t >= p.arr and (p.parent < 0 or procs[p.parent].state == "Terminated"):
                p.state = "SuspReady"; p.event = "release" if p.parent >= 0 else "none"
        resident = [p for p in procs if p.slot and p.state != "Terminated"]
        cand = [p for p in procs if p.state == "SuspReady" and not p.slot]
        while len(resident) < M and cand:
            if s.policy in ("quark", "landed"):
                ql = len(cand); cand.sort(key=lambda p: -score(p, procs, s.dna or DNA0, s.coupled, ql))
            elif s.policy == "hist": cand.sort(key=lambda p: p.est)
            else: cand.sort(key=lambda p: p.arr)
            p = cand.pop(0); p.slot = True; p.state = "Ready"; resident.append(p)
        if s.io_cur is None and s.io_q: s.io_cur = s.io_q.pop(0)
        if s.io_cur is not None:
            s.io_cur.left -= 1
            if s.io_cur.left <= 0:
                c = s.io_cur; c.bi += 1; c.left = c.b[c.bi]; c.state = "Ready"; c.event = "io"; s.io_cur = None
        else: s.io_idle += 1
        if s.run is not None and s.run_q >= Q: s.run.state = "Ready"; s.run.event = "preempt"; s.run = None
        if s.run is None:
            ready = [p for p in procs if p.state == "Ready"]
            if ready: return ready
        return None

    def post(s, chosen):
        if chosen is not None:
            s.run = chosen; s.decisions += 1; s.run.state = "Running"; s.run_q = 0; s.run.wait = 0
        for p in s.procs:
            if p.state == "Ready": p.wait += 1
        r = s.run
        if r is not None:
            r.left -= 1; r.served += 1; s.run_q += 1
            if r.left <= 0:
                burst = r.b[r.bi]; r.prev_est = r.est; r.est = 0.5 * r.est + 0.5 * burst; r.bi += 1
                if r.bi >= len(r.b): r.state = "Terminated"; r.done_t = s.t; r.slot = False
                else: r.left = r.b[r.bi]; r.state = "Waiting"; s.io_q.append(r)
                s.run = None
        s.t += 1

    def step(s):
        ready = s.pre()
        s.post(s.choose(ready) if ready else None)

    def finish(s):
        while s.alive(): s.step()
        return s.G()

    def G(s):
        H = s.horizon
        return -float(np.mean([((p.done_t if p.done_t is not None else H) - p.arr + 1) / p.service for p in s.procs]))

def simulate(d, seed, policy, dna=None, coupled=True, rules=None):
    return World(d, seed, policy, dna, coupled, rules=rules).finish()

# ---- the green tube sphere: exact address first, then the same address with one part dropped -------------------
def coarse_keys(a):
    yield ("exact",) + tuple(map(str, a))
    for drop in range(4):
        yield (f"drop{drop}",) + tuple("*" if i == drop else str(x) for i, x in enumerate(a))

def lookup(rules, a):
    if not rules: return None
    for k in coarse_keys(a):
        r = rules.get("|".join(k))
        if r: return r
    return None

# ---- the channels the turquoise target reads, over the window after the letter --------------------------------
def channels(w, t0, prev_done):
    ready = [p for p in w.procs if p.state == "Ready"]
    done = [p for p in w.procs if p.done_t is not None and p.id not in prev_done]
    return {"wait_sum": sum(p.wait for p in w.procs if p.state in ("Ready",)),       # V: what is seen waiting now
            "max_wait": max([p.wait for p in ready], default=0),                       # O: the trunk (nobody starves)
            "io_idle": w.io_idle,                                                      # A: the device heard idle
            "completed": len(done),                                                    # K: what moved through
            "slow_done": float(sum(((p.done_t - p.arr + 1) / p.service) for p in done))}  # G: how well it was fed

def future(w, chosen_id, H):
    """w is frozen at the letter (after pre()). Copy it, make the choice, run the future."""
    f = copy.deepcopy(w)
    prev = {p.id for p in f.procs if p.done_t is not None}; io0 = f.io_idle
    f.policy = "quark"                      # after the letter the world runs on as the unhealed quark
    f.post(next(p for p in f.procs if p.id == chosen_id))
    for _ in range(H - 1):
        if not f.alive(): break
        f.step()
    c = channels(f, w.t, prev); c["io_idle"] -= io0
    c["G_whole"] = f.finish()               # the whole future of this world, to its end
    return c

def heals(c, c0):
    """U164 turquoise: the whole is better and no channel is worse."""
    better_whole = c["G_whole"] > c0["G_whole"] + 1e-9
    no_worse = (c["max_wait"] <= c0["max_wait"] and c["io_idle"] <= c0["io_idle"] and c["completed"] >= c0["completed"])
    return better_whole and no_worse

if __name__ == "__main__" and sys.argv[1] == "check":
    # the refactored world must reproduce HOLO4's numbers exactly (equivalence before anything is learned)
    import importlib.util
    sp = importlib.util.spec_from_file_location("h4", f"{HERE}/../holo4/holo4.py")
    h4 = importlib.util.module_from_spec(sp); sp.loader.exec_module(h4)
    bad = 0
    for d in DENS:
        for s in [400, 500]:
            for pol in ["rr", "hist", "quark"]:
                a = simulate(d, s, pol, DNA0 if pol == "quark" else None); b = h4.simulate(d, s, pol, DNA0 if pol == "quark" else None)
                bad += abs(a - b) > 1e-12
    print("equivalence mismatches:", bad)

if __name__ == "__main__" and sys.argv[1] == "heal":
    TR = list(range(400, 464)); H = 60; EVERY = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    stats = defaultdict(lambda: defaultdict(lambda: [0, 0]))   # key -> lens -> [heals, tried]
    n_lit = n_read = 0
    for d in DENS:
        for sd in TR:
            w = World(d, sd, "quark", DNA0)
            while w.alive():
                ready = w.pre()                                 # golden light: every tick, every process is lit
                if ready and len(ready) >= 2:
                    n_lit += 1
                    if n_lit % EVERY == 0:
                        frozen = copy.deepcopy(w)               # the present, frozen at the letter
                        picks = {L: frozen.lens_pick(L, [p for p in frozen.procs if p.id in {r.id for r in ready}])
                                 for L in ["rr", "hist", "rel"]}
                        fr_ready = [p for p in frozen.procs if p.id in {r.id for r in ready}]
                        picks["quark"] = frozen.lens_pick("quark", fr_ready)
                        if len({p.id for p in picks.values()}) > 1:
                            n_read += 1
                            addr = frozen.address(fr_ready, picks)          # the letter's unique address
                            # NB: lens_pick("quark") advanced K on the frozen copy; futures start from a fresh copy
                            base = copy.deepcopy(w)
                            futs = {"quark": future(base, picks["quark"].id, H)}
                            for L in ["rr", "hist", "rel"]:
                                if picks[L].id != picks["quark"].id: futs[L] = future(base, picks[L].id, H)
                            c0 = futs["quark"]
                            for L, c in futs.items():
                                if L == "quark": continue
                                for k in coarse_keys(addr):
                                    kk = "|".join(k); stats[kk][L][1] += 1; stats[kk][L][0] += int(heals(c, c0))
                w.post(w.choose(ready) if ready else None)
        print(f"d={d}: letters lit {n_lit}, disagreeing letters read with all futures {n_read}", flush=True)
    # landing rule (sealed in the prereg): a particle lands on an address (or its tube) when one lens heals the whole
    # in at least 60% of the futures read there, with at least 8 futures; the best such lens is the landing
    rules = {}
    for kk, d_ in stats.items():
        best = None
        for L, (h, n) in d_.items():
            if n >= 8 and h / n >= 0.60 and (best is None or h / n > best[1]): best = (L, h / n, n)
        if best: rules[kk] = best[0]
    out = {"rules": rules, "n_letters_lit": n_lit, "n_letters_read": n_read, "H": H, "EVERY": EVERY,
           "stats": {k: {L: v for L, v in d_.items()} for k, d_ in stats.items()},
           "n_rules_exact": sum(1 for k in rules if k.startswith("exact")), "n_rules_tube": sum(1 for k in rules if not k.startswith("exact"))}
    json.dump(out, open(f"{HERE}/LANDINGS.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "stats"}, indent=1))

if __name__ == "__main__" and sys.argv[1] == "test":
    from scipy.stats import binomtest, spearmanr
    L = json.load(open(f"{HERE}/LANDINGS.json")); rules = L["rules"]
    H4 = json.load(open(f"{HERE}/../holo4/DNA_healed.json"))["DNA_healed"]
    TS = list(range(500, 516)); R = {"landings_sha256": hashlib.sha256(open(f"{HERE}/LANDINGS.json", "rb").read()).hexdigest(),
                                     "n_rules": len(rules)}
    A = {k: {} for k in ["landed", "landed_unc", "unhealed", "holo4"]}; MW = {"landed": [], "unhealed": []}; used = []
    for d in DENS:
        rows = []
        for s in TS:
            b = max(simulate(d, s, "rr"), simulate(d, s, "hist"))
            wl = World(d, s, "landed", DNA0, True, rules=rules); gl = wl.finish(); used.append(wl.landed_used / max(1, wl.decisions))
            gu = simulate(d, s, "landed", DNA0, False, rules=rules)
            g0 = simulate(d, s, "quark", DNA0); g4 = simulate(d, s, "quark", H4)
            rows.append((gl - b, gu - b, g0 - b, g4 - b))
        rows = np.array(rows)
        for i, k in enumerate(A): A[k][d] = rows[:, i]
        R[f"d{d}"] = {"adv_landed": float(rows[:, 0].mean()), "adv_landed_uncoupled": float(rows[:, 1].mean()),
                      "adv_unhealed": float(rows[:, 2].mean()), "adv_holo4_healed": float(rows[:, 3].mean()),
                      "landed_wins_vs_best_baseline": int(np.sum(rows[:, 0] > 0))}
    def sp(x): w = int(np.sum(x > 0)); return {"wins": w, "of": len(x), "p": float(binomtest(w, len(x), 0.5, alternative="greater").pvalue)}
    R["W1_landed_beats_best_baseline_d5"] = sp(A["landed"][5])
    rho, p = spearmanr([d for d in DENS for _ in TS], [v for d in DENS for v in A["landed"][d]])
    R["W2_advantage_grows_with_density"] = {"rho": float(rho), "p": float(p)}
    R["W3_coupled_beats_uncoupled_d5"] = sp(A["landed"][5] - A["landed_unc"][5])
    R["W4_landed_beats_unhealed_all"] = sp(np.concatenate([A["landed"][d] - A["unhealed"][d] for d in DENS]))
    R["W5_landing_beats_global_knobs_holo4_all"] = sp(np.concatenate([A["landed"][d] - A["holo4"][d] for d in DENS]))
    R["share_of_decisions_where_a_particle_landed"] = float(np.mean(used))
    json.dump(R, open(f"{HERE}/RESULTS_HOLO5.json", "w"), indent=1); print(json.dumps(R, indent=1))
