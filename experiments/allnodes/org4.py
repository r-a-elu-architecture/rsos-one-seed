"""ORG4: the violet organism with the owner's composition of 22 Nov 2026 02:54 (owner "seal" 02:57), layer 2.
Imports the sealed organism.py (hash-checked against SEAL_ORG1.txt). Composition -> operators:
- White Dragon golden light = the beam (organism.beam), unchanged.
- Library of universal knowledge (past / present / future): one shared store of every shade's round-1 moments.
  Each entry = the situation (6 state features of the shade at that tick: time, mean supply, share drifting, mean
  dryness, worst dryness so far, worst drift duration so far) + the value a landing had there. Value = what the
  joint landing added to the projected whole (future, via forks to the end) over the same picks with all landings
  inside, plus 0.01 x the relief of the worst channel (places where it did not work: channel failure).
  A shade asks the library about its PRESENT situation and gets the value of the 10 most similar moments of OTHER
  shades (never its own entries: that would be memory, not transfer).
- Green particles land where needed, the 3-part helper: a landing in the limited organism is a joint landing:
  supply side + drift side placements (beam) + the channel guard.
- Clean channel guard: a beamed action is accepted only if its projected worst channels are not above those of the
  default action from the SAME current state (the organism's own fork); otherwise the default action. No native
  result is read anywhere.
Tests: m4 transfer (P14'''): limited organism (joint landings on exactly 12 of 60 ticks); library-guided (land when
  the library's predicted value >= its 80th percentile, forced to spend the rest when ticks run out) vs random 12
  ticks (seed 9300). Same picks, same joint landing, same budget: the only difference is the library's knowledge.
  Control (reported): own-shade library only.
  Stronger baseline: "beam-only" = the default picks with the full beam (placement search without the organism's
  where/guard). m3/m5 are against max(best native, beam-only).
  New world types (structurally different dynamics): WB bursts (drift hazard x2.5 in 3 of every 12 ticks);
  WC cascade (second contagion along the drift graph + supply leaking to neighbours). S > best native in each.
  Protocol: exactly 9 of 21 library messages corrupted in transit (seed 9350).
Fresh seeds: round 1 9000-9005, round 2 9100-9105, new worlds 9200-9201.
Not built in ORG4 (said so): the 'unison' gate across neighbour shades (shades are separate worlds here).
Usage: python org4.py round1|round2 <part 0|1>"""
import sys, os, json, copy, hashlib, glob
import numpy as np
os.chdir(os.path.dirname(os.path.abspath(__file__)))
S1 = open("SEAL_ORG1.txt").read()
for f in ("organism.py", "SHADES_v2.json"):
    assert hashlib.sha256(open(f, "rb").read()).hexdigest() in S1, f
import organism as G
O, V3 = G.O, G.V3
R1, R2, RW = list(range(9000, 9006)), list(range(9100, 9106)), [9200, 9201]
BUDGET, K, Q = 12, 10, 80
NV = G.NV; os.makedirs("msg4", exist_ok=True)
BAD = set(int(x) for x in np.random.default_rng(9350).choice(NV, 9, replace=False))

class WB(G.Shade):
    def tick(s, ps, pd, glob=False):
        b = (s.t % 12) < 3
        if b: h0 = s.h; s.h = np.minimum(h0 * 2.5, 0.6)
        super().tick(ps, pd, glob)
        if b: s.h = h0

class WC(G.Shade):
    def tick(s, ps, pd, glob=False):
        super().tick(ps, pd, glob)
        sp = (s.Ad & s.dr[None, :]).sum(1) * 0.04
        s.dr |= (s.rng.random(O.N) < sp) & (s.immune <= 0)
        nb = (s.Ad * s.res[None, :]).sum(1) / np.maximum(1, s.Ad.sum(1)); s.res = 0.85 * s.res + 0.15 * nb

WORLDS = {"main": G.Shade, "WB": WB, "WC": WC}

def feat(w):
    return [w.t / O.T, float(np.mean(w.res)) / 3, float(w.dr.mean()), float(w.dry.mean()) / O.T, w.maxdry / O.T, w.maxd / O.T]

def proj(w, ps, pd, ms, md):
    f = copy.deepcopy(w); f.ms, f.md = dict(ms), dict(md); f.tick(ps, pd); O.to_end(f); return f.G(), f.channels()

def joint(w, p, ps, pd):
    """joint landing: beam both sides, then the clean guard against the default action from the same state."""
    ms, md, _ = G.beam(w, ps, pd, p["modes"])
    gb, cb = proj(w, ps, pd, ms, md)
    ds, dd = O.defaults(w); m0, d0 = {i: "inside" for i in ds}, {j: "inside" for j in dd}
    gd, cd = proj(w, ds, dd, m0, d0)
    if any(a > b for a, b in zip(cb, cd)): return ds, dd, m0, d0, True
    return ps, pd, ms, md, False

def run(W, seed, p, policy, lib=None, rand_ticks=None):
    w = W(seed, p, "tube" if policy == "all" else "inside"); rec = []; guard = 0; spent = 0; prec = []
    thr = np.percentile(lib[1], Q) if lib is not None else None
    while w.t < O.T:
        if isinstance(policy, tuple): w.tick(w.nat("s", policy[0]), w.nat("d", policy[1])); continue
        if policy == "all": w.tick(*V3.org3_picks(w)); continue
        if policy == "B":
            ps, pd = O.defaults(w); ms, md, _ = G.beam(w, ps, pd, p["modes"]); w.ms, w.md = ms, md; w.tick(ps, pd); continue
        ps, pd = V3.org3_picks(w)
        if policy == "Sg":
            x = feat(w); ps, pd, ms, md, gf = joint(w, p, ps, pd); guard += gf
            ins_s, ins_d = {i: "inside" for i in ps}, {j: "inside" for j in pd}
            gi, ci = proj(w, ps, pd, ins_s, ins_d); ga, ca = proj(w, ps, pd, ms, md)
            rec.append(x + [ga - gi + 0.01 * (max(ci) - max(ca))]); w.ms, w.md = ms, md
        elif policy in ("lib", "rand"):
            left_t, left_b = O.T - w.t, BUDGET - spent
            if policy == "rand": go = w.t in rand_ticks
            else:
                if left_b <= 0: go = False
                elif left_t <= left_b: go = True
                else:
                    d = np.linalg.norm(lib[0] - np.array(feat(w)), axis=1); go = lib[1][np.argsort(d)[:K]].mean() >= thr
            if go and spent < BUDGET:
                spent += 1; ps, pd, ms, md, gf = joint(w, p, ps, pd)
                ins_s, ins_d = {i: "inside" for i in ps}, {j: "inside" for j in pd}
                prec.append(proj(w, ps, pd, ms, md)[0] > proj(w, ps, pd, ins_s, ins_d)[0] + 1e-12); w.ms, w.md = ms, md
        w.tick(ps, pd)
    return {"G": float(w.G()), "ch": [float(x) for x in w.channels()], "flows": int(w.flows), "rec": rec, "guard": guard,
            "spent": spent, "precision": float(np.mean(prec)) if prec else None}

def shade_rows(k, seeds):
    node = G.SH["shades"][k]["node"]; v = k + 1; p = G.params(node, v); rows = []
    for sd in seeds:
        nat = {f"{a}+{b}": run(G.Shade, sd, p, (a, b)) for a, b in O.NATS}
        rows.append({"shade": v, "node": node, "seed": sd, "S": run(G.Shade, sd, p, "Sg"), "all": run(G.Shade, sd, p, "all"),
                     "B": run(G.Shade, sd, p, "B"), "nat": nat})
    return rows, p

def worlds(k, p):
    out = []
    for wn in ("WB", "WC"):
        for sd in RW:
            nat = {f"{a}+{b}": run(WORLDS[wn], sd, p, (a, b))["G"] for a, b in O.NATS}
            out.append({"shade": k + 1, "world": wn, "seed": sd, "S": run(WORLDS[wn], sd, p, "Sg")["G"], "nat": nat})
    return out

def send(k, rows):
    rec = sum([r["S"]["rec"] for r in rows], [])
    body = json.dumps({"sender": k + 1, "rec": rec}, sort_keys=True); h = hashlib.sha256(body.encode()).hexdigest()
    bad = k in BAD
    if bad: body = json.dumps({"sender": k + 1, "rec": [x[:6] + [-x[6]] for x in rec]}, sort_keys=True)
    json.dump({"body": body, "sha256": h, "corrupted_in_transit": bad}, open(f"msg4/shade_{k+1:02d}.json", "w"))

def receive():
    msgs, log = {}, {"valid": 0, "rejected_hash": 0, "corrupted_adopted": 0, "corrupted_total": 0, "valid_rejected": 0}
    for f in sorted(glob.glob("msg4/shade_*.json")):
        m = json.load(open(f)); ok = hashlib.sha256(m["body"].encode()).hexdigest() == m["sha256"]
        log["corrupted_total"] += m["corrupted_in_transit"]
        if ok: b = json.loads(m["body"]); msgs[b["sender"]] = np.array(b["rec"]); log["valid"] += 1
        else: log["rejected_hash"] += 1; log["valid_rejected"] += int(not m["corrupted_in_transit"])
        log["corrupted_adopted"] += int(ok and m["corrupted_in_transit"])
    return msgs, log

def library(msgs, include):
    a = np.concatenate([msgs[s] for s in sorted(msgs) if include(s)]); return a[:, :6], a[:, 6]

def round1(ks, tag):
    out, wo = [], []
    for k in ks:
        rows, p = shade_rows(k, R1); out += rows; send(k, rows); wo += worlds(k, p); print(tag, k + 1, flush=True)
    for r in out: r["S"]["rec_n"] = len(r["S"].pop("rec"))
    json.dump({"rows": out, "worlds": wo}, open(f"RAW4_round1_{tag}.json", "w"))

def round2(ks, tag):
    msgs, log = receive(); rng = np.random.default_rng(9300); out = []
    for k in ks:
        v = k + 1; rows, p = shade_rows(k, R2)
        others = library(msgs, lambda s: s != v); own = library(msgs, lambda s: s == v) if v in msgs else None
        for r in rows:
            rt = set(int(x) for x in rng.choice(O.T, BUDGET, replace=False))
            r["lim_library"] = run(G.Shade, r["seed"], p, "lib", lib=others)
            r["lim_random"] = run(G.Shade, r["seed"], p, "rand", rand_ticks=rt)
            r["lim_self"] = run(G.Shade, r["seed"], p, "lib", lib=own) if own is not None else None
            r["S"].pop("rec"); [r[a].pop("rec") for a in ("lim_library", "lim_random") ]
            if r["lim_self"]: r["lim_self"].pop("rec")
        out += rows; print(tag, v, flush=True)
    json.dump({"rows": out, "protocol": log}, open(f"RAW4_round2_{tag}.json", "w"))

if __name__ == "__main__":
    cmd, part = sys.argv[1], int(sys.argv[2])
    {"round1": round1, "round2": round2}[cmd]([k for k in range(NV) if k % 2 == part], f"w{part}")
