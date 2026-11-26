"""ORG2: ORG1 with the four corrections (owner "seal", 21 Nov 2026 19:33). Imports the sealed organism.py and
real_v5.py (hash-checked against SEAL_ORG1.txt); everything not listed here is as ORG1.
1 transfer P14': limited beam with ONE mode trial per landing (imprint-guided vs random-guided)
2 protocol P4b': 40 % of imprint messages corrupted in transit
3 births P16': on each bridge, vary + select over 3 generations (selection seed 8500), then the final child config
  vs both parent configs on fresh test seeds 8600-8602 in the child host
4 temporal placement (real data, P5t): training in 6 blocks of 50 steps; at each block start the beam forks plain
  training to the end of the block under the rate scales 1, 1/2, 1/4, 1/8 (common batches), keeps the best by
  validation log-loss with no class worse; inside the block the v4 placements run at that block's rate.
Fresh seeds: round 1 8300-8305, round 2 8400-8405, real 7950-7957.
Usage: python org2.py round1|round2|births <part 0|1> ; python org2.py real"""
import sys, os, json, copy, hashlib, glob
import numpy as np
os.chdir(os.path.dirname(os.path.abspath(__file__)))
S1 = open("SEAL_ORG1.txt").read()
for f in ("organism.py", "real_v5.py", "SHADES_v2.json"):
    assert hashlib.sha256(open(f, "rb").read()).hexdigest() in S1, f
import organism as G
R1, R2 = list(range(8300, 8306)), list(range(8400, 8406)); SEL, TEST = [8500], list(range(8600, 8603))
NV = G.NV; os.makedirs("msg2", exist_ok=True)

def send(k, rows, rng):
    imp = {}
    for r in rows:
        for m, c in r["S"]["imp"].items(): imp[m] = imp.get(m, 0) + c
    body = json.dumps({"sender": k + 1, "imprint": imp}, sort_keys=True); h = hashlib.sha256(body.encode()).hexdigest()
    bad = bool(rng.random() < 0.40)
    if bad:
        imp2 = {m: (0 if c == max(imp.values()) else c) for m, c in imp.items()}; imp2["inside"] = imp2.get("inside", 0) + 999
        body = json.dumps({"sender": k + 1, "imprint": imp2}, sort_keys=True)
    json.dump({"body": body, "sha256": h, "corrupted_in_transit": bad}, open(f"msg2/shade_{k+1:02d}.json", "w"))

def receive():
    msgs, log = {}, {"valid": 0, "rejected_hash": 0, "corrupted_adopted": 0, "corrupted_total": 0}
    for f in sorted(glob.glob("msg2/shade_*.json")):
        m = json.load(open(f)); ok = hashlib.sha256(m["body"].encode()).hexdigest() == m["sha256"]
        log["corrupted_total"] += m["corrupted_in_transit"]
        if ok: b = json.loads(m["body"]); msgs[b["sender"]] = b["imprint"]; log["valid"] += 1
        else: log["rejected_hash"] += 1
        log["corrupted_adopted"] += int(ok and m["corrupted_in_transit"])
    return msgs, log

def round1(ks, tag):
    rng = np.random.default_rng(abs(hash(tag + "org2")) % 2**32); out = []
    for k in ks:
        rows = G.shade_row(k, R1); out += rows; send(k, rows, rng); print(tag, k + 1, flush=True)
    json.dump(out, open(f"RAW2_round1_{tag}.json", "w"))

def round2(ks, tag):
    msgs, log = receive(); rng = np.random.default_rng(11); out = []
    for k in ks:
        node = G.SH["shades"][k]["node"]; v = k + 1; p = G.params(node, v); order = G.imprint_order(v, msgs, p["modes"])
        for sd in R2:
            nat = {f"{a}+{b}": G.run(sd, p, (a, b)) for a, b in G.O.NATS}
            S = G.run(sd, p, "S"); A = G.run(sd, p, "all")
            rnd = list(rng.permutation([m for m in p["modes"] if m != "inside"]))
            out.append({"shade": v, "node": node, "seed": sd, "S": S, "all": A, "nat": nat, "order": order,
                        "lim_imprint": G.run(sd, p, "lim", order, 1), "lim_random": G.run(sd, p, "lim", rnd, 1)})
        print(tag, v, flush=True)
    json.dump({"rows": out, "protocol": log}, open(f"RAW2_round2_{tag}.json", "w"))

def births(ks, tag):
    out = []; rng = np.random.default_rng(13)
    for k in ks:
        a, b = G.SH["shades"][k]["node"], G.SH["shades"][k + 1]["node"]; pa, pb = G.params(a, k + 1), G.params(b, k + 2)
        pool = sorted(set(pa["modes"]) | set(pb["modes"]) | {"inside"})
        pc = {"d": round((pa["d"] + pb["d"]) / 2), "hz": (pa["hz"] + pb["hz"]) / 2, "cz": (pa["cz"] + pb["cz"]) / 2, "modes": pool}
        fit = lambda ms: np.mean([G.run(s, pc, "S", sorted(ms)) ["G"] for s in SEL])
        pop = [frozenset(pa["modes"]), frozenset(pb["modes"]), frozenset(pool)]; score = {c: fit(c) for c in pop}
        for gen in range(3):
            kids = []
            for c in sorted(score, key=lambda c: -score[c])[:2]:
                m = rng.choice([x for x in pool if x != "inside"]); kid = (c - {m}) if m in c else (c | {m}); kid = frozenset(kid | {"inside"})
                if kid not in score: kids.append(kid)
            for c in kids: score[c] = fit(c)
        best = max(score, key=score.get)
        for sd in TEST:
            out.append({"bridge": f"v{k+1}|v{k+2}", "seed": sd, "best": sorted(best), "child": G.run(sd, pc, "S", sorted(best)),
                        "parentA_cfg": G.run(sd, pc, "S", pa["modes"]), "parentB_cfg": G.run(sd, pc, "S", pb["modes"]),
                        "differs": set(pa["modes"]) != set(pb["modes"])})
        print(tag, k + 1, flush=True)
    json.dump(out, open(f"RAW2_births_{tag}.json", "w"))

def real():
    import real_v5 as Z; R, V4 = Z.R, Z.V4; SEEDS = list(range(7950, 7958)); rows = []
    def run_t(name, seed):
        Xtr, ytr, Xva, yva, Xte, yte, classes = V4.hard(name, seed)
        rng = np.random.default_rng(seed); clf = V4.new(classes, seed, Xtr, ytr)
        batches = [rng.choice(len(Xtr), R.B, replace=False) for _ in range(R.STEPS + 60)]
        mem = np.zeros(len(Xtr)); sched = []
        for blk in range(R.STEPS // 50):
            t0 = blk * 50; best = None
            for sc in (1.0, 0.5, 0.25, 0.125):
                f = copy.deepcopy(clf); f.eta0 = R.LR * sc
                for bb in batches[t0:t0 + 50]: f.partial_fit(Xtr[bb], ytr[bb])
                l, pcl = R.loss(f, Xva, yva, classes).mean(), R.per_class(f, Xva, yva, classes)
                if best is None or (l < best[1] and np.all(pcl >= best[2] - 1e-12)): best = (sc, l, pcl)
            sc = best[0]; sched.append(sc)
            for t in range(t0, t0 + 50):
                idx = batches[t]; lack = R.loss(clf, Xtr, ytr, classes) * (1 + mem); loud = np.argsort(-lack)[:R.K]
                lb = R.loss(clf, Xtr[idx], ytr[idx], classes); keep = idx[np.argsort(lb)[:R.B - R.K]]
                nbrs = []
                for i in loud:
                    same = np.where(ytr == ytr[i])[0]; dd = np.linalg.norm(Xtr[same] - Xtr[i], axis=1); dd[same == i] = np.inf; nbrs.append(same[np.argmin(dd)])
                pc = R.per_class(clf, Xva, yva, classes); pool = np.where(ytr == classes[np.argmin(pc)])[0]
                opts = {"core": idx, "inside": np.concatenate([idx[:R.B - R.K], loud]), "above": np.concatenate([keep, rng.choice(len(Xtr), R.K, replace=False)]),
                        "outside": np.concatenate([idx[:R.B - R.K], np.array(nbrs)]), "tube": np.concatenate([idx[:R.B - R.K], rng.choice(pool, R.K, replace=len(pool) < R.K)])}
                res = {}
                for k2, bt in opts.items():
                    f = copy.deepcopy(clf); f.eta0 = R.LR * sc; f.partial_fit(Xtr[bt], ytr[bt]); ff = copy.deepcopy(f)
                    for bb in batches[t + 1:t + 11]: ff.partial_fit(Xtr[bb], ytr[bb])
                    res[k2] = (f, R.loss(ff, Xva, yva, classes).mean(), R.per_class(ff, Xva, yva, classes))
                bk = "core"
                for k2 in opts:
                    if k2 != "core" and res[k2][1] < res[bk][1] and np.all(res[k2][2] >= res["core"][2] - 1e-12): bk = k2
                clf = res[bk][0]; clf.eta0 = R.LR * sc; mem = 0.9 * mem + (clf.predict(Xtr) != ytr)
        return float(np.mean(clf.predict(Xte) == yte)), sched
    for name in R.DATA:
        for s in SEEDS:
            t, sched = run_t(name, s); r = {p: V4.run(name, s, p)[0] for p in ["plain", "decay", "ohem", "global"]}
            rows.append({"data": name, "seed": s, "temporal": t, "sched": sched, **r, "best_native": max(r["plain"], r["decay"], r["ohem"])})
            print(name, s, round(t - rows[-1]["best_native"], 4), sched, flush=True)
    json.dump(rows, open("RAW2_real.json", "w"))

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "real": real()
    else:
        part = int(sys.argv[2]); tag = f"w{part}"
        if cmd == "births": births([k for k in range(NV - 1) if k % 2 == part], tag)
        else: {"round1": round1, "round2": round2}[cmd]([k for k in range(NV) if k % 2 == part], tag)
