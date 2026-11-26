"""STRUCTURE3 (owner OK 24 Nov 11:09 to IDENT_STRUCTURE3.md: D yes, LE option b). Layer 2. Development quick test, no
colour. Prereg PREREG_STRUCTURE3.md; sealed and pushed before the run. Everything as STRUCTURE2 except:
  D: the child holds its OWN trajectory (K.2 applied to the child; owner 09:54). It keeps the plan it committed to (its own
     future). Each tick every option is valued in each available continuation - its own committed plan and both parents'
     fresh plans - and the child takes the best (option, continuation) and commits to that continuation. Continuing its own
     plan is always an option, so the value it acts on is a future it will actually follow.
  LE: unchanged check (STRUCTURE2's LE with relations); its replays run on 60-tick worlds (option b: the past holds enough
     events); the rest stays at 30 ticks.
  Laws, L5, Meaning, E: code and seeds unchanged from STRUCTURE2 (deterministic) -> carried from RESULT_STRUCTURE2.json,
  not re-run. Usage: python structure3.py part <0|1> ; python structure3.py final"""
import os, sys, copy, json, time
os.environ["S1_T"] = "30"
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import structure2 as S2
M, Q, O, L4, G = S2.M, S2.Q, S2.O, S2.L4, S2.G

def child3(sd, pc, sA, sB):
    w = M.Organs(sd, pc, "inside"); past = {"A": [], "B": []}; src = {}; C = ("lungs", "heart", "kidney"); own = None
    while w.t < O.T:
        acts = {"A": M.decide(w, pc, sA), "B": M.decide(w, pc, sB)}
        plans = {"A": Q.own_plan(w, acts["A"], pc, sA), "B": Q.own_plan(w, acts["B"], pc, sB)}; opts = []
        if own: opts.append(("own", own[0]))
        for k in ("A", "B"):
            opts.append((k + "0", acts[k]))
            for i in (1, 2):
                if len(past[k]) >= i: opts.append((k + "-" + str(i), M.membrane(w, copy.deepcopy(past[k][-i]))))
                if len(plans[k]) >= i: opts.append((k + "+" + str(i), M.membrane(w, copy.deepcopy(plans[k][i - 1]))))
        for x, y in (("A", "B"), ("B", "A")): opts.append(("coupled" + x, Q.compose(w, acts, {o: (x if o in C else y) for o in M.NAMES})))
        conts = ([("own", own[1:])] if own else []) + [("A", plans["A"]), ("B", plans["B"])]
        best = None
        for name, a in opts:
            for cn, pl in conts:
                val = Q.replay(w, a, pl)
                if best is None or val > best[0]: best = (val, name, cn, a, pl)
        _, name, cn, a, pl = best; key = name + "|" + cn; src[key] = src.get(key, 0) + 1; own = list(pl) if pl else None
        for k in ("A", "B"): past[k].append(acts[k])
        w.ms, w.md = a[2], a[3]; w.tick(a[0], a[1])
    return float(w.G()), src

def part(k):
    t0 = time.time(); v = S2.L6.SHADES[k]; sd = 6720; p = G.params(G.SH["shades"][v - 1]["node"], v); st = L4.st_of(v); sB = L4.st_of(v + 1); pc = M.params_both(v)
    out = {"v": v}; out["child"], out["child_src"] = child3(sd, pc, st, sB)
    out["parents"] = [M.run_parent(M.Organs, sd, pc, s)["G"] for s in (st, sB)]; out["best_parent"] = max(out["parents"]); print("D", v, round(time.time() - t0), flush=True)
    O.T = 60; out["LE_rel_T60"] = S2.le_rel(v, S2.L6.SEEDS[0]); O.T = 30
    out["sec"] = round(time.time() - t0); json.dump(out, open(f"diag/S3_part{k}.json", "w"), default=float, indent=1)
    print(json.dumps({x: y for x, y in out.items() if x != "LE_rel_T60"}, default=float), flush=True)

def final():
    R2 = json.load(open("diag/RESULT_STRUCTURE2.json")); P = [json.load(open(f"diag/S3_part{k}.json")) for k in (0, 1)]
    C = dict(R2["checks"]); le = [r for x in P for r in x["LE_rel_T60"]]
    C["LE_relations"] = all(r["ok"] for r in le) and len(le) > 0; C["D_B1"] = all(x["child"] > x["best_parent"] for x in P)
    S = {"checks": C, "TABLE_FILLED": all(C.values()), "carried_from_STRUCTURE2": [k for k in C if k not in ("LE_relations", "D_B1")],
         "D": [{k: x[k] for k in ("v", "child", "parents", "best_parent", "child_src")} for x in P], "LE_rel_T60": le}
    json.dump(S, open("diag/RESULT_STRUCTURE3.json", "w"), default=float, indent=1); print(json.dumps(C, indent=1), "\nTABLE_FILLED", S["TABLE_FILLED"])

if __name__ == "__main__":
    part(int(sys.argv[2])) if sys.argv[1] == "part" else final()
