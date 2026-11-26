"""SEC1 v3 organism: correction of the v2 build defect (interdependence built as a veto).
Imports the sealed sec1_org.py (hash-checked) for the world, natives, global, apart and spread; changes only the
organism dragon:
  - shared gain: a single landing is kept when the WHOLE organism is better at the end and no channel is worse
    (the other host may lose locally: the tube shares, it does not veto);
  - all dots connected: the organism reads three whole programs for the tick: (A) its own best landings by whole
    gain, (B) each host's own best landings (the apart program, which is part of the organism's knowledge),
    (C) the default; each is forked and run to the end; the one with the best whole (channels not worse) lands.
    Ties go to B. Disclosed: B is inside the candidate set, so P7 tests whether reading the whole adds anything
    beyond the hosts' own programs.
Fresh seeds 7400-7415, densities 1-5. Usage: python sec1_org_v3.py run 1,2"""
import sys, json, copy, hashlib
import numpy as np
import sec1_org as O
H_ORG = hashlib.sha256(open("sec1_org.py", "rb").read()).hexdigest()
assert H_ORG in open("SEAL_SEC1.txt").read(), "sec1_org.py changed since seal"
SEEDS = list(range(7400, 7416))

def org3_picks(w):
    ds, dd = O.defaults(w)
    r = copy.deepcopy(w); r.tick(ds, dd); O.to_end(r); g0, ch0 = r.G(), r.channels()
    cand = [("s", int(i)) for i in dict.fromkeys(list(np.argsort(-w.lack_s())[:O.M]) + [int(x) for x in w.nat("s", "round")])] + \
           [("d", int(j)) for j in dict.fromkeys(list(np.argsort(-w.lack_d())[:O.M]) + [int(x) for x in w.nat("d", "round")])]
    sc = []
    for host, u in cand:
        f = copy.deepcopy(w)
        ps = [u] + [x for x in ds if x != u][:O.KH - 1] if host == "s" else ds
        pd = [u] + [x for x in dd if x != u][:O.KH - 1] if host == "d" else dd
        f.tick(ps, pd); O.to_end(f)
        if f.G() > g0 and all(a <= b for a, b in zip(f.channels(), ch0)):
            sc.append((f.G() - g0, host, u, (f.Gs() < r.Gs()) if host == "s" else (f.Gd() < r.Gd())))
    sc.sort(reverse=True); ps, pd, tp = [], [], 0
    for g, host, u, ll in sc:
        if len(ps) + len(pd) >= 2 * O.KH: break
        (ps if host == "s" else pd).append(u); tp += int(ll)
    fs = [x for x in ds if x not in ps]; fd = [x for x in dd if x not in pd]
    while len(ps) + len(pd) < 2 * O.KH:
        if fs and (len(ps) <= len(pd) or not fd): ps.append(fs.pop(0))
        elif fd: pd.append(fd.pop(0))
        else: break
    progs = {"B": O.apart_picks(w), "A": (ps, pd), "C": (ds, dd)}
    best, bg = "B", None
    for k, (a, b) in progs.items():
        f = copy.deepcopy(w); f.tick(a, b); O.to_end(f)
        if k != "B" and not all(x <= y for x, y in zip(f.channels(), ch0)): continue
        if bg is None or f.G() > bg + 1e-12: best, bg = k, f.G()
    if best == "A": w.transpersonal += tp
    w.choice = getattr(w, "choice", {"A": 0, "B": 0, "C": 0}); w.choice[best] += 1
    return progs[best]

def run3(seed, d):
    w = O.Org(seed, d, True)
    while w.t < O.T: w.tick(*org3_picks(w))
    return w.G(), w.transpersonal, w.choice

if __name__ == "__main__" and sys.argv[1] == "run":
    dens = [int(x) for x in sys.argv[2].split(",")]
    rows = []
    for d in dens:
        for sd in SEEDS:
            nat = {f"{a}+{b}": O.run(sd, d, (a, b))[0] for a, b in O.NATS}
            go, tp, ch = run3(sd, d)
            rows.append({"d": d, "seed": sd, "organism": go, "transpersonal": tp, "choice": ch, "apart": O.run(sd, d, "apart")[0],
                         "global": O.run(sd, d, "global")[0], "unhealed": nat["report+popular"], "best_native": max(nat.values()),
                         "spread_on": O.spread(sd, d, True), "spread_off": O.spread(sd, d, False)})
            print(d, sd, round(go - rows[-1]["unhealed"], 4), round(go - rows[-1]["apart"], 4), ch, flush=True)
    json.dump(rows, open(f"RAW_SEC1v3_org_{'_'.join(map(str, dens))}.json", "w"))
