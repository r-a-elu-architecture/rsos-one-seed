"""ORG3: the violet organism with the three corrections that follow from ORG2 (owner "seal", 22 Nov 2026 01:46).
Imports the sealed organism.py (hash-checked against SEAL_ORG1.txt); world, shades, natives, picks and beam unchanged.
1 transfer P14'' (m4): the imprint carries WHERE (host side s/d) and WHEN (time bin of 5 ticks) the beam's landings
  paid off (a non-inside placement adopted), not which placement. Limited organism: beam on only 12 of 60 ticks, on
  one host side per tick. Imprint-guided = cells (bin, side) ranked by the other shades' imprints (two-sign rule,
  weight 1/(1+|dv|)); random-guided = the same procedure with cells in random order (seed 8900). Every node with at
  least one non-inside placement can differ, so the test has power wherever the beam can act.
2 channel guard (m2): S reads the native twin's realised worst channels (one shadow run of report+popular, same seed)
  and accepts its beamed action only if the projected worst channels stay <= the twin's; otherwise the default
  action with all landings inside; if both exceed, the one with the smaller worst excess. Disclosed: the guard reads
  the native twin of the same world (layer-2 twin, U-shadow); nothing else changes.
3 protocol P4b'': exactly 9 of the 21 imprint messages are corrupted in transit (shades fixed by seed 8950).
Births are out of ORG3 (waiting for the owner's picture). P5t (real data) is carried from ORG2 (passed, sealed run).
Fresh seeds: round 1 8700-8705, round 2 8800-8805.
Usage: python org3.py round1|round2 <part 0|1>"""
import sys, os, json, copy, hashlib, glob
import numpy as np
os.chdir(os.path.dirname(os.path.abspath(__file__)))
S1 = open("SEAL_ORG1.txt").read()
for f in ("organism.py", "SHADES_v2.json"):
    assert hashlib.sha256(open(f, "rb").read()).hexdigest() in S1, f
import organism as G
O, V3 = G.O, G.V3
R1, R2 = list(range(8700, 8706)), list(range(8800, 8806)); BUDGET, BIN = 12, 5; NB = O.T // BIN
NV = G.NV; os.makedirs("msg3", exist_ok=True)
BAD = set(int(x) for x in np.random.default_rng(8950).choice(NV, 9, replace=False))

def beam_side(w, ps, pd, order, side):
    """the organism's beam (organism.beam), acting on one host side only; the other side stays inside."""
    ms, md = {i: "inside" for i in ps}, {j: "inside" for j in pd}; n = 0
    def fut():
        f = copy.deepcopy(w); f.ms, f.md = dict(ms), dict(md); f.tick(ps, pd); O.to_end(f); return f.G(), f.channels()
    g0, ch0 = fut()
    for u in (ps if side == "s" else pd):
        D = ms if side == "s" else md; cur = D[u]
        for m in order:
            if m == "inside": continue
            D[u] = m; g, ch = fut()
            if g > g0 + 1e-12 and all(a <= b for a, b in zip(ch, ch0)): g0, ch0, cur = g, ch, m
            D[u] = cur
        n += D[u] != "inside"
    return ms, md, n

def proj(w, ps, pd, ms, md):
    f = copy.deepcopy(w); f.ms, f.md = dict(ms), dict(md); f.tick(ps, pd); O.to_end(f); return f.channels()

def run3(seed, p, policy, chN=None, plan=None):
    w = G.Shade(seed, p, "inside"); hist = np.zeros((NB, 2)); guard = 0
    while w.t < O.T:
        ps, pd = V3.org3_picks(w)
        if policy == "Sg":
            ms, md, _ = G.beam(w, ps, pd, p["modes"])
            ex = lambda ch: max(a - b for a, b in zip(ch, chN))
            e1 = ex(proj(w, ps, pd, ms, md))
            if e1 > 0:
                ds, dd = O.defaults(w); m0, d0 = {i: "inside" for i in ds}, {j: "inside" for j in dd}
                e2 = ex(proj(w, ds, dd, m0, d0))
                if e2 <= 0 or e2 < e1: ps, pd, ms, md = ds, dd, m0, d0; guard += 1
            b = min(w.t // BIN, NB - 1)
            hist[b, 0] += sum(m != "inside" for m in ms.values()); hist[b, 1] += sum(m != "inside" for m in md.values())
            w.ms, w.md = ms, md
        elif policy == "lim":
            if w.t in plan:
                ms, md, _ = beam_side(w, ps, pd, p["modes"], plan[w.t]); w.ms, w.md = ms, md
        w.tick(ps, pd)
    return {"G": float(w.G()), "ch": [float(x) for x in w.channels()], "flows": int(w.flows), "hist": hist.tolist(), "guard": guard}

def shade_rows(k, seeds):
    node = G.SH["shades"][k]["node"]; v = k + 1; p = G.params(node, v); rows = []
    for sd in seeds:
        nat = {f"{a}+{b}": G.run(sd, p, (a, b)) for a, b in O.NATS}
        rows.append({"shade": v, "node": node, "seed": sd, "S": run3(sd, p, "Sg", chN=nat["report+popular"]["ch"]),
                     "all": G.run(sd, p, "all"), "nat": nat})
    return rows, p

def send(k, rows):
    hist = np.sum([r["S"]["hist"] for r in rows], 0).tolist()
    body = json.dumps({"sender": k + 1, "hist": hist}, sort_keys=True); h = hashlib.sha256(body.encode()).hexdigest()
    bad = k in BAD
    if bad: body = json.dumps({"sender": k + 1, "hist": hist[::-1]}, sort_keys=True)
    json.dump({"body": body, "sha256": h, "corrupted_in_transit": bad}, open(f"msg3/shade_{k+1:02d}.json", "w"))

def receive():
    msgs, log = {}, {"valid": 0, "rejected_hash": 0, "corrupted_adopted": 0, "corrupted_total": 0, "valid_rejected": 0}
    for f in sorted(glob.glob("msg3/shade_*.json")):
        m = json.load(open(f)); ok = hashlib.sha256(m["body"].encode()).hexdigest() == m["sha256"]
        log["corrupted_total"] += m["corrupted_in_transit"]
        if ok: b = json.loads(m["body"]); msgs[b["sender"]] = np.array(b["hist"]); log["valid"] += 1
        else: log["rejected_hash"] += 1; log["valid_rejected"] += int(not m["corrupted_in_transit"])
        log["corrupted_adopted"] += int(ok and m["corrupted_in_transit"])
    return msgs, log

def cells_imprint(v, msgs):
    score = np.zeros((NB, 2)); signs = np.zeros((NB, 2))
    for s, h in msgs.items():
        if s == v or h.sum() == 0: continue
        score += (h / h.sum()) / (1 + abs(s - v)); signs += h > 0
    score = np.where(signs >= 2, score, -1)
    return sorted(((b, c) for b in range(NB) for c in range(2)), key=lambda x: -score[x])

def plan_from(cells):
    plan = {}
    for b, c in cells:
        for t in range(b * BIN, min(O.T, (b + 1) * BIN)):
            if len(plan) >= BUDGET: return plan
            plan.setdefault(t, "sd"[c])
    return plan

def round1(ks, tag):
    out = []
    for k in ks:
        rows, _ = shade_rows(k, R1); out += rows; send(k, rows); print(tag, k + 1, flush=True)
    json.dump(out, open(f"RAW3_round1_{tag}.json", "w"))

def round2(ks, tag):
    msgs, log = receive(); rng = np.random.default_rng(8900); out = []
    allcells = [(b, c) for b in range(NB) for c in range(2)]
    for k in ks:
        v = k + 1; rows, p = shade_rows(k, R2); pi = plan_from(cells_imprint(v, msgs))
        for r in rows:
            pr = plan_from([allcells[i] for i in rng.permutation(len(allcells))])
            r["lim_imprint"] = run3(r["seed"], p, "lim", plan=pi); r["lim_random"] = run3(r["seed"], p, "lim", plan=pr)
            r["plan_imprint"] = sorted(pi.items()); r["plan_random"] = sorted(pr.items())
        out += rows; print(tag, v, flush=True)
    json.dump({"rows": out, "protocol": log}, open(f"RAW3_round2_{tag}.json", "w"))

if __name__ == "__main__":
    cmd, part = sys.argv[1], int(sys.argv[2])
    {"round1": round1, "round2": round2}[cmd]([k for k in range(NV) if k % 2 == part], f"w{part}")
