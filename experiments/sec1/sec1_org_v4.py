"""SEC1 v4 organism host: U167 turquoise at places of need (owner, 21 Nov 2026 15:41).
Imports the sealed sec1_org.py and sec1_org_v3.py (hash-checked). Same coupled supply + drift world; the lack is read
by the turquoise core everywhere (live readings). What differs is WHERE and HOW particles land:
  modes for a supply landing at i (budget 0.6 each):
    inside  : 0.6 into i                         above   : shield i from consumption for 2 ticks (no change of state)
    outside : 0.6 to i's neighbours by lack      pierced : 0.3 into i + heal the linked drift unit i (both hosts)
    line    : 0.3 into i + 0.3 to its neediest neighbour (one directed link)
    tube    : the v2/v3 sphere-tube (half to neighbours by lack, cross-host heal) = the all-to-all landing
  modes for a drift landing at j:
    inside  : heal j                             above   : j cannot drift for 3 ticks (no change of state)
    outside : heal j's most popular drifted neighbour (else j)
    pierced : heal j + 0.2 reserve to linked supply unit j
    line    : heal j + heal its most popular drifted neighbour
    tube    : the v2/v3 sphere-tube (line + 0.2 reserve)
Policies (all choose WHERE with the v3 organism dragon, run inside each policy's own world):
  all     : every landing is a tube (U166 all-to-all; = v3)
  sparse  : core lands inside; the dragon's beam then picks the mode of each landing (6 modes, each forked to the
            end of the world, best whole with no channel worse; ties keep the current mode)  (U167)
  inside  : core lands inside, no mode choice
  natives : report+popular, round+round, random+random, inside mode
P0 sparse > unhealed (report+popular); P5 sparse > best native; P8 sparse > all; P9 sparse > inside;
P3' Spearman(density, sparse - all) > 0 (precision over density). Cost: non-inside flows per world.
Fresh seeds 7600-7615 x densities 1, 3, 5. Usage: python sec1_org_v4.py run 1"""
import sys, json, copy, hashlib
import numpy as np
import sec1_org as O, sec1_org_v3 as V3
for f in ("sec1_org.py", "sec1_org_v3.py"):
    assert hashlib.sha256(open(f, "rb").read()).hexdigest() in open("SEAL_SEC1.txt").read(), f
SEEDS = list(range(7600, 7616)); MODES = ["inside", "above", "outside", "pierced", "line", "tube"]

class Org4(O.Org):
    def __init__(s, seed, d, default):
        super().__init__(seed, d, True); s.dm = default; s.ms, s.md = {}, {}
        s.shield = np.zeros(O.N); s.immune = np.zeros(O.N); s.flows = 0
    def dose(s, i, amt=0.6):
        m = s.ms.get(i, s.dm); s.flows += m != "inside"
        nb = np.where(s.As[i])[0]
        if m == "tube": return O.Org.dose(s, i, amt)
        if m == "above": s.shield[i] = 2
        elif m == "outside" and len(nb):
            l = np.maximum(0, 1.0 - s.res[nb]); w = l / l.sum() if l.sum() > 0 else np.ones(len(nb)) / len(nb); s.res[nb] += amt * w
        elif m == "pierced":
            s.res[i] = max(s.res[i], 0) + amt / 2
            if s.dr[i]: s.dr[i] = False; s.dur[i] = 0; s.events[i] += 1
        elif m == "line" and len(nb):
            s.res[i] = max(s.res[i], 0) + amt / 2; k = nb[np.argmin(s.res[nb])]; s.res[k] = max(s.res[k], 0) + amt / 2
        else: s.res[i] = max(s.res[i], 0) + amt
        s.res[i] = min(3.0, s.res[i]); s.last[i] = s.t
    def heal(s, j):
        m = s.md.get(j, s.dm); s.flows += m != "inside"
        nbd = np.where(s.Ad[j] & s.dr)[0]
        if m == "tube": return O.Org.heal(s, j)
        if m == "above": s.immune[j] = 3; return
        if m == "outside" and len(nbd): j = nbd[np.argmax(s.pop[nbd])]
        if s.dr[j]: s.events[j] += 1
        s.dr[j] = False; s.since[j] = 0; s.dur[j] = 0
        if m == "pierced": s.res[j] = min(3.0, s.res[j] + 0.2)
        if m == "line" and len(nbd): k = nbd[np.argmax(s.pop[nbd])]; s.dr[k] = False; s.dur[k] = 0; s.events[k] += 1
    def tick(s, ps, pd, glob=False):
        s.t += 1; s.since += 1
        c = s.c0 * (1 + 0.5 * s.dr) * (s.shield <= 0); s.res -= c
        if glob: s.res += len(ps) * 0.6 / O.N
        else:
            for i in ps: s.dose(i)
        s.res = np.minimum(s.res, 3.0); wk = s.res > 0; s.dry = np.where(wk, 0, s.dry + 1)
        s.work += wk.mean(); s.maxdry = max(s.maxdry, s.dry.max())
        h = s.h * (1 + (s.res <= 0)); spread = (s.Ad & s.dr[None, :]).sum(1) * 0.02
        s.dr |= (s.rng.random(O.N) < h + spread) & (s.immune <= 0)
        if glob:
            for j in s.rng.choice(O.N, len(pd), replace=False): s.dr[j] = False; s.since[j] = 0
        else:
            for j in pd: s.heal(j)
        for j in s.rng.choice(O.N, 20, p=s.pop):
            s.n += 1
            if s.dr[j]: s.dr[j] = False
            else: s.ok += 1
        s.dur = np.where(s.dr, s.dur + 1, 0); s.maxd = max(s.maxd, s.dur.max())
        s.shield = np.maximum(0, s.shield - 1); s.immune = np.maximum(0, s.immune - 1); s.ms, s.md = {}, {}

def beam(w, ps, pd):
    """The White Dragon's beam: for each landing, the placement mode whose future (to the end) is best for the whole."""
    ms, md = {i: "inside" for i in ps}, {j: "inside" for j in pd}
    def fut():
        f = copy.deepcopy(w); f.ms, f.md = dict(ms), dict(md); f.tick(ps, pd); O.to_end(f); return f.G(), f.channels()
    g0, ch0 = fut()
    for host, u in [("s", i) for i in ps] + [("d", j) for j in pd]:
        D = ms if host == "s" else md; cur = D[u]
        for m in MODES:
            if m == cur: continue
            D[u] = m; g, ch = fut()
            if g > g0 + 1e-12 and all(a <= b for a, b in zip(ch, ch0)): g0, ch0, cur = g, ch, m
            D[u] = cur
    return ms, md

def run4(seed, d, policy):
    w = Org4(seed, d, "tube" if policy == "all" else "inside"); modes = {m: 0 for m in MODES}
    while w.t < O.T:
        if policy in ("all", "sparse", "inside"):
            ps, pd = V3.org3_picks(w)
            if policy == "sparse":
                ms, md = beam(w, ps, pd); w.ms, w.md = ms, md
                for m in list(ms.values()) + list(md.values()): modes[m] += 1
            w.tick(ps, pd)
        else: w.tick(w.nat("s", policy[0]), w.nat("d", policy[1]))
    return w.G(), w.flows, modes

if __name__ == "__main__" and sys.argv[1] == "run":
    rows = []
    for d in [int(x) for x in sys.argv[2].split(",")]:
        for sd in SEEDS:
            nat = {f"{a}+{b}": run4(sd, d, (a, b))[0] for a, b in O.NATS}
            gs, fs, md = run4(sd, d, "sparse"); ga, fa, _ = run4(sd, d, "all"); gi, _, _ = run4(sd, d, "inside")
            rows.append({"d": d, "seed": sd, "sparse": gs, "all": ga, "inside": gi, "unhealed": nat["report+popular"],
                         "best_native": max(nat.values()), "flows_sparse": int(fs), "flows_all": int(fa), "modes": md})
            print(d, sd, round(gs - ga, 4), round(gs - gi, 4), fs, fa, md, flush=True)
    json.dump(rows, open(f"RAW_SEC1v4_org_{sys.argv[2].replace(',', '_')}.json", "w"))
