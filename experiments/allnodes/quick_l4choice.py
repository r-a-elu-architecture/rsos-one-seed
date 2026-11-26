"""QUICK_L4CHOICE (24 Nov 09:32; v2 09:42: D options add the organ combinations of the parents, complementation): one law for Meaning, D, E: choose the option by Law 4 need = the organism's own
forked future (common randomness, defaults to the end). Very quick look, dev seed 6720, shades 4, 10, 16. No colour."""
import sys, copy, json, time, numpy as np, organs as M
O, F4, L4 = M.O, M.F4, M.L4
def fut(w, a):
    f = copy.deepcopy(w); f.ms, f.md = a[2], a[3]; f.tick(a[0], a[1]); O.to_end(f); return f.G()
def pick(w, opts):
    return max(opts, key=lambda a: fut(w, a))
def house(sd, p, st):
    w = M.Organs(sd, p, "inside")
    while w.t < O.T:
        a = pick(w, [M.decide(w, p, st)] + [M.room_action(w, p, st, k, None) for k in M.NAMES]); w.ms, w.md = a[2], a[3]; w.tick(a[0], a[1])
    return w.G()
def compose(w, acts, book):
    d = M.deficit(w); order = sorted(M.NAMES, key=lambda k: -d[k]); cs, cd = [], []
    for side, out in ((0, cs), (1, cd)):
        for k in order:
            for u in acts[book[k]][side]:
                if u in M.ORG[k] and u not in out: out.append(u)
    ps, pd, i = [], [], 0
    while len(ps) + len(pd) < 2 * O.KH and (i < len(cs) or i < len(cd)):
        if i < len(cs) and len(ps) + len(pd) < 2 * O.KH: ps.append(cs[i])
        if i < len(cd) and len(ps) + len(pd) < 2 * O.KH: pd.append(cd[i])
        i += 1
    ms = {u: acts["A"][2].get(u, acts["B"][2].get(u, "inside")) for u in ps}; md = {u: acts["A"][3].get(u, acts["B"][3].get(u, "inside")) for u in pd}
    return M.membrane(w, [ps, pd, ms, md])
def child(sd, pc, sA, sB):
    w = M.Organs(sd, pc, "inside")
    while w.t < O.T:
        acts = {"A": M.decide(w, pc, sA), "B": M.decide(w, pc, sB)}; opts = [acts["A"], acts["B"]]
        for k in M.NAMES:
            for base, other in (("A", "B"), ("B", "A")): opts.append(compose(w, acts, {j: (other if j == k else base) for j in M.NAMES}))
        a = pick(w, opts); w.ms, w.md = a[2], a[3]; w.tick(a[0], a[1])
    return w.G()
def living(sd, p, st):
    w = M.Living(sd, p, "inside")
    while w.t < O.T:
        b = M.decide(w, p, st); a = pick(w, [b] + [M.membrane(w, M.focus(w, copy.deepcopy(b), k, 1, 1)) for k in M.NAMES]); w.ms, w.md = a[2], a[3]; w.tick(a[0], a[1])
    return w.G()
v = int(sys.argv[1]); sd = 6720; p = M.G.params(M.G.SH["shades"][v-1]["node"], v); st = L4.st_of(v); sB = L4.st_of(v+1); pc = M.params_both(v)
t = time.time(); r = {"v": v}
r["house"] = house(sd, p, st); r["best_single"] = max(M.run_house(M.Organs, sd, p, st, "single", k)["G"] for k in M.NAMES)
r["child"] = child(sd, pc, st, sB); r["best_parent"] = max(M.run_parent(M.Organs, sd, pc, s)["G"] for s in (st, sB))
r["living"] = living(sd, p, st); r["v3"] = M.run_parent(M.Living, sd, p, st)["G"]
r["best_native"] = max([F4.run(M.Living, sd, p, n)["G"] for n in O.NATS] + [F4.run(M.Living, sd, p, "B")["G"]])
r["sec"] = round(time.time() - t); print(json.dumps(r), flush=True)

# v3 09:50: D's future measured as K.2 requires: the organism's own policy, not defaults. The child's own policy = its
# parents' policies; per tick record one closed-loop future under each parent (common randomness), then replay each plan
# open-loop after every option; option value = the better of the two replays (cheap replay need, K.5).
def own_plan(w, a0, p, st):
    f = copy.deepcopy(w); f.ms, f.md = a0[2], a0[3]; f.tick(a0[0], a0[1]); rec = []
    while f.t < O.T:
        a = M.decide(f, p, st); rec.append(a); f.ms, f.md = a[2], a[3]; f.tick(a[0], a[1])
    return rec
def replay(w, a, plan):
    f = copy.deepcopy(w); f.ms, f.md = a[2], a[3]; f.tick(a[0], a[1])
    for b in plan:
        if f.t >= O.T: break
        f.ms, f.md = b[2], b[3]; f.tick(b[0], b[1])
    return f.G()
def child_own(sd, pc, sA, sB):
    w = M.Organs(sd, pc, "inside")
    while w.t < O.T:
        acts = {"A": M.decide(w, pc, sA), "B": M.decide(w, pc, sB)}; opts = [acts["A"], acts["B"]]
        for k in M.NAMES:
            for base, other in (("A", "B"), ("B", "A")): opts.append(compose(w, acts, {j: (other if j == k else base) for j in M.NAMES}))
        plans = [own_plan(w, acts["A"], pc, sA), own_plan(w, acts["B"], pc, sB)]
        a = max(opts, key=lambda o: max(replay(w, o, pl) for pl in plans)); w.ms, w.md = a[2], a[3]; w.tick(a[0], a[1])
    return w.G()

# v4 09:57 (owner 09:54): the parents are trajectories (past, present, future). The child's options = each parent's action
# at t, at t-1 and t-2 (its recorded past) and at t+1 and t+2 (its own future plan), all applied now; Law 4 chooses
# (own-policy futures, cheap replay, membrane). Same structure, time-shifted trajectory.
def child_time(sd, pc, sA, sB):
    w = M.Organs(sd, pc, "inside"); past = {"A": [], "B": []}; src = {}
    while w.t < O.T:
        acts = {"A": M.decide(w, pc, sA), "B": M.decide(w, pc, sB)}
        plans = {"A": own_plan(w, acts["A"], pc, sA), "B": own_plan(w, acts["B"], pc, sB)}
        opts = []
        for k in ("A", "B"):
            opts.append((k + "0", acts[k]))
            for i in (1, 2):
                if len(past[k]) >= i: opts.append((k + "-" + str(i), M.membrane(w, copy.deepcopy(past[k][-i]))))
                if len(plans[k]) >= i: opts.append((k + "+" + str(i), M.membrane(w, copy.deepcopy(plans[k][i - 1]))))
        name, a = max(opts, key=lambda o: max(replay(w, o[1], pl) for pl in plans.values()))
        src[name] = src.get(name, 0) + 1
        for k in ("A", "B"): past[k].append(acts[k])
        w.ms, w.md = a[2], a[3]; w.tick(a[0], a[1])
    return w.G(), src
