"""ORG1: the violet organism (U168-U171) with the 18:06 program (map/ORGANISM_PROGRAM_21NOV_1806.md), layer 2.
Shade hosts: each of the 21 shades (SHADES_v2.json) is a layer-2 twin built from ONE world template (the coupled
supply+drift world of sec1_org/sec1_org_v4, hash-checked) whose parameters come from the node's own structure
(main laws, particle placements) and its shade v. Disclosed: twins are section-level hosts generated from the
structure map, not domain simulations. Centre S = v3 dragon (where) + beam over the node's own placements (how).
Arms per shade and seed: S (full beam over the node's placements), natives (report+popular, round+round,
random+random; inside mode), all (sphere-tube everywhere). Round 2 adds the limited beam (2 mode trials per
landing) guided by imprints from other shades (U109/U143) vs by random modes. Imprints travel as messages between
2 worker processes (U149/U110/U125): sha256-proofed, 10 % corrupted in transit on purpose; adopted only if the hash
holds and 2 independent senders agree. Children (U139/U170): a shade born on each bridge v_i|v_i+1.
Usage: python organism.py round1|round2|children|all"""
import sys, json, copy, hashlib, os, glob
import numpy as np
os.chdir(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, "../sec1")
SEALS = open("../sec1/SEAL_SEC1.txt").read()
for f in ("sec1_org.py", "sec1_org_v3.py", "sec1_org_v4.py"):
    assert hashlib.sha256(open("../sec1/" + f, "rb").read()).hexdigest() in SEALS, f
cwd = os.getcwd(); os.chdir("../sec1")
import sec1_org as O, sec1_org_v3 as V3, sec1_org_v4 as V4
os.chdir(cwd)
O.N, O.T = 30, 60
SH = json.load(open("SHADES_v2.json")); NV = len(SH["shades"])
src = open("shades.py").read(); FEAT = eval(src[src.index("N = {") + 4: src.index("}\nnames") + 1])
R1, R2, RC = list(range(8000, 8006)), list(range(8100, 8106)), list(range(8200, 8203))

def params(node, v):
    laws, pl = FEAT[node].split("|"); laws, pl = laws.split(","), pl.split(",")
    return {"d": 1 + 2 * ("L5" in laws) + ("tube" in pl), "hz": 1 + 0.5 * bool({"ERR", "L2"} & set(laws)) + 0.5 * v / NV,
            "cz": 1 + 0.5 * ("L4" in laws) + 0.5 * (1 - v / NV), "modes": sorted(set(pl) | {"inside"})}

class Shade(V4.Org4):
    def __init__(s, seed, p, default):
        super().__init__(seed, p["d"], default); s.h = np.minimum(s.h * p["hz"], 0.5); s.c0 = s.c0 * p["cz"]

def beam(w, ps, pd, order, K=None):
    ms, md = {i: "inside" for i in ps}, {j: "inside" for j in pd}; counts = {}
    def fut():
        f = copy.deepcopy(w); f.ms, f.md = dict(ms), dict(md); f.tick(ps, pd); O.to_end(f); return f.G(), f.channels()
    g0, ch0 = fut()
    for host, u in [("s", i) for i in ps] + [("d", j) for j in pd]:
        D = ms if host == "s" else md; cur = D[u]; tried = 0
        for m in order:
            if m == "inside": continue
            if K is not None and tried >= K: break
            tried += 1; D[u] = m; g, ch = fut()
            if g > g0 + 1e-12 and all(a <= b for a, b in zip(ch, ch0)): g0, ch0, cur = g, ch, m
            D[u] = cur
        counts[D[u]] = counts.get(D[u], 0) + 1
    return ms, md, counts

def run(seed, p, policy, order=None, K=None):
    w = Shade(seed, p, "tube" if policy == "all" else "inside"); imp = {}
    while w.t < O.T:
        if policy in ("S", "lim"):
            ps, pd = V3.org3_picks(w); ms, md, c = beam(w, ps, pd, order or p["modes"], K); w.ms, w.md = ms, md
            for k, v in c.items(): imp[k] = imp.get(k, 0) + v
            w.tick(ps, pd)
        elif policy == "all":
            ps, pd = V3.org3_picks(w); w.tick(ps, pd)
        else: w.tick(w.nat("s", policy[0]), w.nat("d", policy[1]))
    return {"G": float(w.G()), "ch": [float(x) for x in w.channels()], "flows": int(w.flows), "imp": imp}

def shade_row(k, seeds):
    node = SH["shades"][k]["node"]; v = k + 1; p = params(node, v); rows = []
    for sd in seeds:
        nat = {f"{a}+{b}": run(sd, p, (a, b)) for a, b in O.NATS}
        S, A = run(sd, p, "S"), run(sd, p, "all")
        rows.append({"shade": v, "node": node, "seed": sd, "S": S, "all": A, "nat": nat})
    return rows

def send(k, rows, rng):
    imp = {}
    for r in rows:
        for m, c in r["S"]["imp"].items(): imp[m] = imp.get(m, 0) + c
    body = json.dumps({"sender": k + 1, "imprint": imp}, sort_keys=True); h = hashlib.sha256(body.encode()).hexdigest()
    corrupted = bool(rng.random() < 0.10)
    if corrupted and imp:
        top = max(imp, key=imp.get); imp2 = dict(imp); imp2[top] = 0; imp2["inside"] = imp2.get("inside", 0) + 999
        body = json.dumps({"sender": k + 1, "imprint": imp2}, sort_keys=True)
    json.dump({"body": body, "sha256": h, "corrupted_in_transit": corrupted}, open(f"msg/shade_{k+1:02d}.json", "w"))

def worker(ks, tag):
    rng = np.random.default_rng(hash(tag) % 2**32); os.makedirs("msg", exist_ok=True); out = []
    for k in ks:
        rows = shade_row(k, R1); out += rows; send(k, rows, rng); print(tag, k + 1, flush=True)
    json.dump(out, open(f"RAW_round1_{tag}.json", "w"))

def receive():
    msgs, log = {}, {"valid": 0, "rejected_hash": 0, "corrupted_adopted": 0, "corrupted_total": 0}
    for f in sorted(glob.glob("msg/shade_*.json")):
        m = json.load(open(f)); ok = hashlib.sha256(m["body"].encode()).hexdigest() == m["sha256"]
        log["corrupted_total"] += m["corrupted_in_transit"]
        if ok: msgs[json.loads(m["body"])["sender"]] = json.loads(m["body"])["imprint"]; log["valid"] += 1
        else: log["rejected_hash"] += 1
        log["corrupted_adopted"] += int(ok and m["corrupted_in_transit"])
    return msgs, log

def imprint_order(v, msgs, modes):
    """two-sign: a mode is ranked by imprint only if at least 2 senders (other shades) chose it; weight 1/(1+|dv|)."""
    score = {m: 0.0 for m in modes}; signs = {m: 0 for m in modes}
    for s, imp in msgs.items():
        if s == v: continue
        tot = sum(imp.values()) or 1
        for m, c in imp.items():
            if m in score and m != "inside" and c > 0: score[m] += (c / tot) / (1 + abs(s - v)); signs[m] += 1
    ranked = [m for m in sorted(score, key=lambda m: -score[m]) if m != "inside" and signs[m] >= 2]
    return ranked + [m for m in modes if m not in ranked and m != "inside"]

def round2(ks, tag):
    msgs, log = receive(); rng = np.random.default_rng(7); out = []
    for k in ks:
        node = SH["shades"][k]["node"]; v = k + 1; p = params(node, v); order = imprint_order(v, msgs, p["modes"])
        for sd in R2:
            nat = {f"{a}+{b}": run(sd, p, (a, b)) for a, b in O.NATS}
            S = run(sd, p, "S"); A = run(sd, p, "all")
            rnd = [m for m in rng.permutation([m for m in p["modes"] if m != "inside"])]
            LI, LR = run(sd, p, "lim", order, 2), run(sd, p, "lim", rnd, 2)
            out.append({"shade": v, "node": node, "seed": sd, "S": S, "all": A, "nat": nat, "lim_imprint": LI, "lim_random": LR, "order": order})
        print(tag, v, flush=True)
    json.dump({"rows": out, "protocol": log}, open(f"RAW_round2_{tag}.json", "w"))

def children(ks, tag):
    out = []
    for k in ks:
        a, b = SH["shades"][k]["node"], SH["shades"][k + 1]["node"]
        pa, pb = params(a, k + 1), params(b, k + 2)
        pc = {"d": round((pa["d"] + pb["d"]) / 2), "hz": (pa["hz"] + pb["hz"]) / 2, "cz": (pa["cz"] + pb["cz"]) / 2,
              "modes": sorted(set(pa["modes"]) | set(pb["modes"]))}
        for sd in RC:
            out.append({"bridge": f"v{k+1}|v{k+2}", "seed": sd, "child": run(sd, pc, "S", pc["modes"]),
                        "parentA_cfg": run(sd, pc, "S", pa["modes"]), "parentB_cfg": run(sd, pc, "S", pb["modes"]),
                        "differs": set(pa["modes"]) != set(pb["modes"])})
        print(tag, k + 1, flush=True)
    json.dump(out, open(f"RAW_children_{tag}.json", "w"))

if __name__ == "__main__":
    cmd, part = sys.argv[1], int(sys.argv[2]); ks = [k for k in range(NV) if k % 2 == part]
    {"round1": worker, "round2": round2}.get(cmd, lambda ks, t: children([k for k in range(NV - 1) if k % 2 == part], t))(ks, f"w{part}")
