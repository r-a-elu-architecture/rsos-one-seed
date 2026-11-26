"""REAL1 SEED: the one structure of layer 2 (STRUCTURE1-6), unchanged in every real host. Layer 1 test. Owner OK 24 Nov
2026 13:10. One file, one hash; every host binds to it through the Host interface below; nothing in this file is tuned per
host.

THE STRUCTURE (as filled in layer 2)
  Branches the unit holds at each step:
    present  : the host's own standard action now (its default policy)
    past     : the seed's own actions at t-1, t-2 (re-applied now)
    future   : the seed's own committed plan at t+1, t+2 (taken now: anticipation)
    space    : focused actions offered by the host (resource concentrated on one part)
    relations: coupled actions offered by the host (parts that drive each other, together)
  One operator (Law 4, K.2): each branch is valued in the unit's OWN future: the host is forked, the branch is applied,
  and the continuation is followed to the horizon.
  LAYER 1 RULE (fixed 24 Nov 13:20, before any real host): nothing can fork the real world. A fork never carries the real
  step's randomness: it is the host's own model run with independent randomness (fork sample j of this decision). All
  branches of one decision share the same samples (a fair comparison); the real step never sees them. The value of a
  branch = mean over host.samples forks. Two
  continuations are available: the seed's own committed plan (its own trajectory, D) and a fresh rollout of the host's
  standard policy. The best (branch, continuation) is taken and the seed commits to that continuation.
  Membrane (Law 0): the chosen branch must be at least as good as the host's standard action in the same forked future;
  otherwise the standard action is taken.
  Value: the host's own objective at the horizon. 14:00 (owner 13:34; before any seal): the value matches the row's pass
  rule. For free-resource rows (pass = Pareto) the objective is the pair (result, -resource), compared lexicographically:
  result first, then less resource; for priced and fixed-budget rows it is the result.

THE HOST INTERFACE (every binding implements exactly these; nothing else is read by the seed)
  reset(cell)            -> state                 a fresh episode for one cell (seed number)
  done(state)            -> bool
  default(state)         -> action                the host's standard method's action (the baseline AND the membrane bound)
  branches(state)        -> [(name, action)]      focused / coupled actions the host offers (may be [])
  valid(state, action)   -> action                the action made feasible in this state (budget, constraints)
  step(state, action)    -> state                 the real transition (the host's own randomness inside state)
  fork(state, j)         -> state                 a copy for model sample j of this decision: the host's own model with
                                                  randomness independent of the real step (never the real future)
  samples                : int                    model samples per decision (>= 1)
  objective(state)       -> float                 the host's value of where it stands (higher is better)
  report(state)          -> dict                  {"result": float, "resource": float, ...} for the measure R
  horizon                : int                    steps the own future looks ahead (the episode length if feasible)
Usage: from seed import run; run(host, cell, "seed" | "default")
"""
import copy
TREE = 8   # 14:15 (owner 13:45): the own future is read on the TREE, not a leaf: every branch is valued over at least 8
           # model futures in every host (one rule for all rows; the host may ask for more, never fewer)

def _rollout(host, s, first, plan=None, horizon=None):
    """Apply `first` to model forks of s (samples j = 0..samples-1, independent of the real step), then follow `plan` or
    the host's standard policy; return (mean objective at the horizon, actions taken after `first` in sample 0)."""
    H = host.horizon if horizon is None else horizon; vals = []; taken0 = []
    for j in range(max(TREE, getattr(host, "samples", 1))):
        f = host.fork(s, j); f = host.step(f, host.valid(f, first)); taken = []; h = 0
        while not host.done(f) and h < H:
            a = plan[h] if (plan is not None and h < len(plan)) else host.default(f)
            a = host.valid(f, a); taken.append(a); f = host.step(f, a); h += 1
        vals.append(host.objective(f))
        if j == 0: taken0 = taken
    if isinstance(vals[0], tuple):   # lexicographic value (result first, then the row's second criterion), mean per component
        return tuple(sum(v[k] for v in vals) / len(vals) for k in range(len(vals[0]))), taken0
    return sum(vals) / len(vals), taken0

def choose(host, s, past, own):
    present = host.default(s)
    cand = [("present", present)]
    for i in (1, 2):
        if len(past) >= i: cand.append((f"past-{i}", past[-i]))
    if own:
        for i in (1, 2):
            if len(own) >= i: cand.append((f"future+{i}", own[i - 1]))
    cand += list(host.branches(s))
    conts = ([("own", own[1:] if own else [])] if own else []) + [("standard", None)]
    base_val = {}
    best = None
    for cname, plan in conts:
        bv, _ = _rollout(host, s, present, plan)
        base_val[cname] = bv
    for name, a in cand:
        a = host.valid(s, a)
        for cname, plan in conts:
            v, taken = _rollout(host, s, a, plan)
            if v < base_val[cname]: continue                       # membrane: never worse than the standard action
            if best is None or v > best[0]: best = (v, name, cname, a, taken)
    if best is None: return "present", "standard", host.valid(s, present), []
    _, name, cname, a, taken = best
    return name, cname, a, taken

def _val(host, s, a, plan):
    return _rollout(host, s, a, plan)[0]

def land(host, s, a, plan):
    """LAW 4 LANDING (24 Nov 19:30, owner: 'land where it is needed'): each landing of the chosen action is tested in the
    same own futures, with it vs without it. No need -> withhold (resource saved); more need elsewhere -> retarget to the
    part with the highest need. Hosts that do not offer landings() are left unchanged."""
    if not hasattr(host, "landings"): return a, {"withheld": 0, "retargeted": 0}
    ev = {"withheld": 0, "retargeted": 0}; cur = host.valid(s, a); v_cur = _val(host, s, cur, plan)
    for L in list(host.landings(s, cur)):
        if L not in host.landings(s, cur): continue
        wo = host.valid(s, host.without(s, cur, L)); v_wo = _val(host, s, wo, plan)
        best, v_best, kind = None, v_wo, "withheld"
        for T in host.targets(s, cur, L):
            rt = host.valid(s, host.retarget(s, cur, L, T)); v_rt = _val(host, s, rt, plan)
            if v_rt > v_best: best, v_best, kind = rt, v_rt, "retargeted"
        if kind == "withheld" and v_wo >= v_cur: cur, v_cur = wo, v_wo; ev["withheld"] += 1          # no need: withhold
        elif kind == "retargeted" and v_best > v_cur: cur, v_cur = best, v_best; ev["retargeted"] += 1  # more need elsewhere
    return cur, ev

def run(host, cell, mode="seed"):
    s = host.reset(cell); past = []; own = []; trace = {}
    while not host.done(s):
        if mode == "default":
            a = host.valid(s, host.default(s)); key = "present|standard"
        elif mode == "rollout":   # PLAIN ROLLOUT baseline (Bertsekas): present + host branches, standard continuation only
            cand = [("present", host.default(s))] + list(host.branches(s)); base_v = _val(host, s, host.default(s), None)
            key, a = "present|standard", host.valid(s, host.default(s))
            for nm, b in cand:
                vb = _val(host, s, host.valid(s, b), None)
                if vb > base_v: base_v, key, a = vb, f"{nm}|rollout", host.valid(s, b)
        else:
            name, cname, a, own = choose(host, s, past, own); key = f"{name}|{cname}"
            if mode == "seed":   # the seed WITH the landing step; mode "seed_noland" = REAL1's seed (choice only)
                a, ev = land(host, s, a, own[:] if own else None)
                for q, n in ev.items(): trace["land_" + q] = trace.get("land_" + q, 0) + n
        trace[key] = trace.get(key, 0) + 1
        past.append(a); s = host.step(s, a)
    out = dict(host.report(s)); out["choices"] = trace
    out["R"] = out["result"] / out["resource"] if out.get("resource") else out["result"]
    return out
