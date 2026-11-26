"""SEC1 v2 build 1: the turquoise organism (U166) over the supply and drift hosts (TOP_MAP_SEC1_v2.md).
The two hosts are coupled in the world for every policy: a dry supply unit doubles the drift hazard of its linked drift
unit; a drifted drift unit raises the consumption of its linked supply unit by 50 %.
Spheres and tubes (live=True): a landing flows along the relations inside its host (as sec1_net) AND through the tube to
the linked unit of the other host (supply dose heals the linked drifted unit; drift heal gives +0.2 reserve); the lack
is read from memory and from the other host's state. live=False: no flows, no memory, no cross-host reading.
Organism dragon (the ten parameters as builds): candidates from every lens of both hosts (collective intelligence);
each candidate forked and run to the end of the world (long-term); scored by the organism's whole = mean of both hosts
(holistic, global); rejected if it makes the other host worse than the reference (interdependence) or any channel
worse (dynamic balance); landings allocated freely across hosts within the shared budget of 8 per tick (systems
integration, ecological: never more than the per-tick regeneration); local-loss-for-organism-gain landings logged
(transpersonal). Evolutionary perspective (clone + re-entry) is built in the discovery host (P6), not here.
Apart: each host has its own dragon, 4 landings per tick, scoring only its own host (same budget in total).
Usage: python sec1_org.py run [densities]"""
import sys, json, copy, hashlib
import numpy as np

N, KH, T, M = 40, 2, 120, 6
SEEDS = list(range(7200, 7216)); DENS = [1, 2, 3, 4, 5]

def graph(rng, d):
    A = np.zeros((N, N), bool)
    for _ in range(N * d):
        i, j = rng.integers(N, size=2)
        if i != j: A[i, j] = A[j, i] = True
    return A

class Org:
    def __init__(s, seed, d, live):
        r = np.random.default_rng(seed); s.rng = np.random.default_rng(seed + 1); s.live = live
        s.As, s.Ad = graph(r, d), graph(r, d)
        s.c0 = r.lognormal(np.log(0.05) - 0.32, 0.8, size=N); s.res = r.uniform(0.5, 2.0, size=N)
        s.dry = np.zeros(N); s.last = np.zeros(N); s.work = 0.0; s.maxdry = 0.0
        s.h = r.beta(0.3, 12, size=N); pop = 1.0 / np.arange(1, N + 1) ** 1.1; r.shuffle(pop); s.pop = pop / pop.sum()
        s.dr = np.zeros(N, bool); s.since = np.zeros(N); s.events = np.zeros(N); s.dur = np.zeros(N)
        s.ok = s.n = 0; s.maxd = 0.0; s.t = 0; s.transpersonal = 0
    # ---- lack (memory and the other host's state when live) ----
    def lack_s(s):
        if s.live: return s.c0 * (1 + 0.5 * s.dr) * (s.t - s.last) + (s.res <= 0) * (1 + s.dry / 10)
        return (s.res <= 0).astype(float) + 1e-3 * s.rng.random(N)
    def lack_d(s):
        if s.live:
            hz = (1 + s.events) / (21 + s.since.sum() / N)
            return (1 - (1 - hz) ** (s.since + 1)) * (1 + 0.1 * (s.Ad @ s.dur)) * (1 + (s.res <= 0)) * (s.pop * N)
        return s.pop * N + 1e-6 * s.rng.random(N)
    # ---- landings ----
    def dose(s, i, amt=0.6):
        if s.live:
            if s.As[i].any():
                nb = np.where(s.As[i])[0]; l = np.maximum(0, 1.0 - s.res[nb]); share = 0.5 * amt
                if l.sum() > 0: s.res[nb] += share * l / l.sum(); amt -= share
            if s.dr[i]: s.dr[i] = False; s.dur[i] = 0; s.events[i] += 1          # tube to the other host
        s.res[i] = min(3.0, max(s.res[i], 0) + amt); s.last[i] = s.t
    def heal(s, j):
        if s.dr[j]: s.events[j] += 1
        s.dr[j] = False; s.since[j] = 0; s.dur[j] = 0
        if s.live:
            nb = np.where(s.Ad[j] & s.dr)[0]
            if len(nb): k = nb[np.argmax(s.pop[nb])]; s.dr[k] = False; s.dur[k] = 0; s.events[k] += 1
            s.res[j] = min(3.0, s.res[j] + 0.2)                                    # tube to the other host
    # ---- one tick of the coupled world ----
    def tick(s, ps, pd, glob=False):
        s.t += 1; s.since += 1
        c = s.c0 * (1 + 0.5 * s.dr)                                                 # coupling drift -> supply
        s.res -= c
        if glob: s.res += len(ps) * 0.6 / N
        else:
            for i in ps: s.dose(i)
        s.res = np.minimum(s.res, 3.0); wk = s.res > 0; s.dry = np.where(wk, 0, s.dry + 1)
        s.work += wk.mean(); s.maxdry = max(s.maxdry, s.dry.max())
        h = s.h * (1 + (s.res <= 0))                                                # coupling supply -> drift
        spread = (s.Ad & s.dr[None, :]).sum(1) * 0.02
        s.dr |= s.rng.random(N) < h + spread
        if glob:
            for j in s.rng.choice(N, len(pd), replace=False): s.dr[j] = False; s.since[j] = 0
        else:
            for j in pd: s.heal(j)
        for j in s.rng.choice(N, 20, p=s.pop):
            s.n += 1
            if s.dr[j]: s.dr[j] = False
            else: s.ok += 1
        s.dur = np.where(s.dr, s.dur + 1, 0); s.maxd = max(s.maxd, s.dur.max())
    def Gs(s): return s.work / max(1, s.t)
    def Gd(s): return s.ok / max(1, s.n)
    def G(s): return 0.5 * (s.Gs() + s.Gd())
    def channels(s): return (s.maxdry, s.maxd)
    def nat(s, host, name, k=KH):
        if host == "s":
            if name == "report": return list(np.argsort(s.res + 1e-9 * s.rng.random(N))[:k])
            if name == "round": return list(np.argsort(s.last + 1e-9 * s.rng.random(N))[:k])
        else:
            if name == "popular": return list(np.argsort(-s.pop)[:k])
            if name == "round": return list(np.argsort(-s.since + 1e-9 * s.rng.random(N))[:k])
        return list(s.rng.choice(N, k, replace=False))

def defaults(w): return w.nat("s", "report"), w.nat("d", "popular")

def to_end(f):
    while f.t < T: f.tick(*defaults(f))
    return f

def org_picks(w):
    ds, dd = defaults(w)
    r = copy.deepcopy(w); r.tick(ds, dd); to_end(r); g0, gs0, gd0, ch0 = r.G(), r.Gs(), r.Gd(), r.channels()
    cand = [("s", int(i)) for i in dict.fromkeys(list(np.argsort(-w.lack_s())[:M]) + [int(x) for x in w.nat("s", "round")])] + \
           [("d", int(j)) for j in dict.fromkeys(list(np.argsort(-w.lack_d())[:M]) + [int(x) for x in w.nat("d", "round")])]
    scored = []
    for host, u in cand:
        f = copy.deepcopy(w)
        ps = [u] + [x for x in ds if x != u][:KH - 1] if host == "s" else ds
        pd = [u] + [x for x in dd if x != u][:KH - 1] if host == "d" else dd
        f.tick(ps, pd); to_end(f)
        other_ok = (f.Gd() >= gd0) if host == "s" else (f.Gs() >= gs0)                # interdependence
        ch_ok = all(a <= b for a, b in zip(f.channels(), ch0))                       # dynamic balance
        if other_ok and ch_ok and f.G() > g0:
            local_loss = (f.Gs() < gs0) if host == "s" else (f.Gd() < gd0)
            scored.append((f.G() - g0, host, u, local_loss))
    scored.sort(reverse=True)
    ps, pd = [], []
    for g, host, u, ll in scored:
        if len(ps) + len(pd) >= 2 * KH: break
        (ps if host == "s" else pd).append(u); w.transpersonal += int(ll)
    fill_s = [x for x in ds if x not in ps]; fill_d = [x for x in dd if x not in pd]
    while len(ps) + len(pd) < 2 * KH:                                                  # the shared budget of 8
        if fill_s and (len(ps) <= len(pd) or not fill_d): ps.append(fill_s.pop(0))
        elif fill_d: pd.append(fill_d.pop(0))
        else: break
    return ps, pd

def apart_picks(w):
    ds, dd = defaults(w); out = []
    for host, lack, d0 in (("s", w.lack_s(), ds), ("d", w.lack_d(), dd)):
        r = copy.deepcopy(w); r.tick(ds, dd); to_end(r); g0 = r.Gs() if host == "s" else r.Gd(); ch0 = r.channels()
        cand = list(dict.fromkeys([int(i) for i in np.argsort(-lack)[:M]] + [int(x) for x in w.nat(host, "round")]))
        sc = []
        for u in cand:
            f = copy.deepcopy(w)
            if host == "s": f.tick([u] + [x for x in ds if x != u][:KH - 1], dd)
            else: f.tick(ds, [u] + [x for x in dd if x != u][:KH - 1])
            to_end(f); g = f.Gs() if host == "s" else f.Gd()
            if g > g0 and all(a <= b for a, b in zip(f.channels(), ch0)): sc.append((g - g0, u))
        sc.sort(reverse=True); p = [u for _, u in sc][:KH]; p += [x for x in d0 if x not in p][:KH - len(p)]
        out.append(p)
    return out[0], out[1]

def run(seed, d, policy, live=True):
    w = Org(seed, d, live)
    while w.t < T:
        if policy == "organism": w.tick(*org_picks(w))
        elif policy == "apart": w.tick(*apart_picks(w))
        elif policy == "global": w.tick(list(range(KH)), list(range(KH)), glob=True)
        else: w.tick(w.nat("s", policy[0]), w.nat("d", policy[1]))
    return w.G(), w.transpersonal

def spread(seed, d, live):
    w = Org(seed, d, live)
    for _ in range(40): w.tick(*defaults(w))
    a, b = copy.deepcopy(w), copy.deepcopy(w); i = int(np.argmin(w.res)); b.dose(i)
    for _ in range(20):
        a.tick(a.nat("s", "random"), a.nat("d", "random")); b.tick(b.nat("s", "random"), b.nat("d", "random"))
    return int(np.sum(np.abs(a.res - b.res) > 1e-9) + np.sum(a.dr != b.dr))

NATS = [("report", "popular"), ("round", "round"), ("random", "random")]

if __name__ == "__main__" and sys.argv[1] == "run":
    dens = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else DENS
    rows = []
    for d in dens:
        for sd in SEEDS:
            nat = {f"{a}+{b}": run(sd, d, (a, b))[0] for a, b in NATS}
            go, tp = run(sd, d, "organism")
            rows.append({"d": d, "seed": sd, "organism": go, "transpersonal": tp, "apart": run(sd, d, "apart")[0],
                         "global": run(sd, d, "global")[0], "unhealed": nat["report+popular"], "best_native": max(nat.values()),
                         **{f"n_{k}": v for k, v in nat.items()}, "spread_on": spread(sd, d, True), "spread_off": spread(sd, d, False)})
            print(d, sd, round(go - rows[-1]["unhealed"], 4), round(go - rows[-1]["apart"], 4), flush=True)
    json.dump(rows, open(f"RAW_SEC1v2_org_{'_'.join(map(str, dens))}.json", "w"))
