"""SEC1, network hosts (supply = H2 native dynamics, drift = H1 native dynamics), section law L* (TOP_MAP_SEC1.md).
One engine, the same operators in every host:
  relations at density d (world)                         U151, U13x
  live channels: a landing flows along the relations to the linked nodes by their lack   U112, U162, vakog.spread
  memory: the lack is read from the node's history (time since last landing, past events)  U133, living structure
  exact landing read against the futures: every candidate place is forked and run forward    U159-U163, U50, U56
  turquoise gate: the whole better and no channel worse                                      U164
  global change of the same size: the same budget spread over every node                     (HOLO4-style knobs)
Predictions P0, P1, P2, P3, P5 of TOP_MAP_SEC1.md. P4 and P6 are not measurable in these hosts (reported as such).
Usage: python sec1_net.py run"""
import sys, json, copy, hashlib
import numpy as np

N, K, T, H, M = 60, 4, 200, 20, 12
SEEDS = list(range(7000, 7016))
DENS = [1, 2, 3, 4, 5]

def graph(rng, d):
    A = np.zeros((N, N), bool)
    for _ in range(N * d):                          # mean degree 2d
        i, j = rng.integers(N, size=2)
        if i != j: A[i, j] = A[j, i] = True
    return A

class Supply:
    """H2: each node consumes its reserve; a landing is a dose; a dry node does not work."""
    name = "supply"
    def __init__(s, seed, d, live):
        r = np.random.default_rng(seed); s.rng = np.random.default_rng(seed + 1)
        s.A = graph(r, d); s.live = live
        s.c = r.lognormal(np.log(0.05) - 0.32, 0.8, size=N); s.res = r.uniform(0.5, 2.0, size=N)
        s.dry = np.zeros(N); s.last = np.zeros(N); s.t = 0; s.work = 0.0; s.maxdry = 0.0
    def lack(s):
        if s.live: return s.c * (s.t - s.last) + (s.res <= 0) * (1 + s.dry / 10)   # memory: history of use
        return (s.res <= 0).astype(float) + 1e-3 * s.rng.random(N)                  # no memory: only what is dry now
    def dose(s, i, amt=0.6):
        if s.live and s.A[i].any():                 # live channel: the landing flows to linked nodes by their lack
            nb = np.where(s.A[i])[0]; l = np.maximum(0, 1.0 - s.res[nb]); share = 0.5 * amt
            if l.sum() > 0:
                s.res[nb] += share * l / l.sum(); amt -= share
        s.res[i] = min(3.0, max(s.res[i], 0) + amt); s.last[i] = s.t
    def tick(s, picks, glob=False):
        s.t += 1; s.res -= s.c
        if glob: s.res += K * 0.6 / N
        else:
            for i in picks: s.dose(i)
        s.res = np.minimum(s.res, 3.0)
        wk = s.res > 0; s.dry = np.where(wk, 0, s.dry + 1)
        s.work += wk.mean(); s.maxdry = max(s.maxdry, s.dry.max())
    def G(s): return s.work / max(1, s.t)
    def channels(s): return {"maxdry": s.maxdry}
    def native(s, name):
        if name == "report": return list(np.argsort(s.res + 1e-9 * s.rng.random(N))[:K])
        if name == "round": return list(np.argsort(s.last + 1e-9 * s.rng.random(N))[:K])
        return list(s.rng.choice(N, K, replace=False))

class Drift:
    """H1: items drift and drift spreads along relations; a used drifted item fails; a landing checks and heals."""
    name = "drift"
    def __init__(s, seed, d, live):
        r = np.random.default_rng(seed); s.rng = np.random.default_rng(seed + 1)
        s.A = graph(r, d); s.live = live; s.d = d
        s.h = r.beta(0.3, 12, size=N); pop = 1.0 / np.arange(1, N + 1) ** 1.1; r.shuffle(pop); s.pop = pop / pop.sum()
        s.dr = np.zeros(N, bool); s.since = np.zeros(N); s.events = np.zeros(N); s.t = 0; s.ok = s.n = 0; s.maxd = 0.0
        s.dur = np.zeros(N)
    def lack(s):
        if s.live:
            hz = (1 + s.events) / (21 + s.since.sum() / N)
            nb = s.A @ s.dur                                         # neighbours long drifted raise the risk
            return (1 - (1 - hz) ** (s.since + 1)) * (1 + 0.1 * nb) * (s.pop * N)
        return s.pop * N + 1e-6 * s.rng.random(N)
    def heal(s, i):
        if s.dr[i]: s.events[i] += 1
        s.dr[i] = False; s.since[i] = 0; s.dur[i] = 0
        if s.live:                                                   # live channel: the heal flows through the tubes
            nb = np.where(s.A[i] & s.dr)[0]
            if len(nb): j = nb[np.argmax(s.pop[nb])]; s.dr[j] = False; s.dur[j] = 0; s.events[j] += 1
    def tick(s, picks, glob=False):
        s.t += 1; s.since += 1
        spread = (s.A & s.dr[None, :]).sum(1) * 0.02
        s.dr |= s.rng.random(N) < s.h + spread
        if glob:
            for i in s.rng.choice(N, K, replace=False):              # the same budget, blind to place
                s.dr[i] = False; s.since[i] = 0
        else:
            for i in picks: s.heal(i)
        for i in s.rng.choice(N, 20, p=s.pop):
            s.n += 1
            if s.dr[i]: s.dr[i] = False
            else: s.ok += 1
        s.dur = np.where(s.dr, s.dur + 1, 0); s.maxd = max(s.maxd, s.dur.max())
    def G(s): return s.ok / max(1, s.n)
    def channels(s): return {"maxdrift": s.maxd}
    def native(s, name):
        if name == "popular": return list(np.argsort(-s.pop)[:K])
        if name == "round": return list(np.argsort(-s.since + 1e-9 * s.rng.random(N))[:K])
        return list(s.rng.choice(N, K, replace=False))

HOSTS = {"supply": (Supply, ["report", "round", "random"]), "drift": (Drift, ["popular", "round", "random"])}

def default(w):
    return w.native(HOSTS[w.name][1][0])

def dragon_picks(w):
    """Exact landing: candidates by lack (memory), each forked and run H ticks into the future; the turquoise gate."""
    base = default(w)
    cand = list(dict.fromkeys(list(np.argsort(-w.lack())[:M]) + base))
    ref = copy.deepcopy(w); ref.tick(base)
    for _ in range(H - 1): ref.tick(default(ref))
    g0, ch0 = ref.G(), ref.channels()
    gains = []
    for c in cand:
        f = copy.deepcopy(w); f.tick([c] + [b for b in base if b != c][:K - 1])
        for _ in range(H - 1): f.tick(default(f))
        ch = f.channels()
        if all(ch[k] <= ch0[k] for k in ch): gains.append((f.G() - g0, c))
    gains.sort(reverse=True)
    picks = [c for g, c in gains if g > 0][:K]
    return picks + [b for b in base if b not in picks][:K - len(picks)]

def run(host, seed, d, policy, live=True):
    cls, _ = HOSTS[host]; w = cls(seed, d, live)
    for _ in range(T):
        if policy == "dragon": w.tick(dragon_picks(w))
        elif policy == "global": w.tick([], glob=True)
        else: w.tick(w.native(policy))
    return w.G()

def spread_of_one_landing(host, seed, d, live):
    """P1: how far one landing moves the whole: nodes whose state differs H ticks after one extra landing."""
    cls, nat = HOSTS[host]; w = cls(seed, d, live)
    for _ in range(50): w.tick(w.native(nat[0]))
    a, b = copy.deepcopy(w), copy.deepcopy(w)
    i = int(np.argmax(w.lack()))
    b.dose(i) if host == "supply" else b.heal(i)
    for _ in range(H):
        a.tick(a.native("random")); b.tick(b.native("random"))     # identical rngs: only the landing differs
    if host == "supply": return int(np.sum(np.abs(a.res - b.res) > 1e-9))
    return int(np.sum(a.dr != b.dr) + np.sum(np.abs(a.since - b.since) > 0))

if __name__ == "__main__" and sys.argv[1] == "run":
    from scipy.stats import binomtest, spearmanr
    def sp(x): x = np.asarray(x); w = int(np.sum(x > 0)); return {"wins": w, "of": len(x), "p": float(binomtest(w, len(x), 0.5, alternative="greater").pvalue)}
    R = {"code_sha256": hashlib.sha256(open(__file__, "rb").read()).hexdigest()}
    for host, (cls, nat) in HOSTS.items():
        if len(sys.argv) > 2 and host != sys.argv[2]: continue
        rows = []
        for d in DENS:
            for s in SEEDS:
                g = {p: run(host, s, d, p) for p in nat}
                rows.append({"d": d, "seed": s, "dragon": run(host, s, d, "dragon"), "global": run(host, s, d, "global"),
                             "unhealed": g[nat[0]], "best_native": max(g.values()), **{f"n_{k}": v for k, v in g.items()},
                             "spread_live": spread_of_one_landing(host, s, d, True),
                             "spread_off": spread_of_one_landing(host, s, d, False)})
            print(host, d, flush=True)
        a = lambda k1, k2: [r[k1] - r[k2] for r in rows]
        gain = [r["dragon"] - r["unhealed"] for r in rows]
        rho, p = spearmanr([r["d"] for r in rows], gain)
        R[host] = {"P0_exact_beats_unhealed": sp(a("dragon", "unhealed")),
                   "P1_spreads_further_with_living_structure": sp(a("spread_live", "spread_off")),
                   "P2_exact_beats_global_same_size": sp(a("dragon", "global")),
                   "P3_gain_grows_with_density": {"rho": float(rho), "p": float(p)},
                   "P5_beats_best_native": sp(a("dragon", "best_native")),
                   "means_by_d": {d: {k: float(np.mean([r[k] for r in rows if r["d"] == d])) for k in ["dragon", "global", "unhealed", "best_native", "spread_live", "spread_off"]} for d in DENS},
                   "P4": "not measurable in this host", "P6": "not measurable in this host"}
        json.dump(rows, open(f"RAW_SEC1_{host}.json", "w"))
    json.dump(R, open(f"RESULTS_SEC1_{sys.argv[2] if len(sys.argv) > 2 else 'net'}.json", "w"), indent=1); print(json.dumps(R, indent=1))
