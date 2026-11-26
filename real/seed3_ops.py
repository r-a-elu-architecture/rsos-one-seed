"""REAL3 v2 SEED OPERATORS (owner 25 Nov 00:13, "go"): every RSOS operator written once, with one computational meaning
valid in every row, bound to a row through a few OPTIONAL host hooks (real/HOST_INTERFACE_REAL3v2.md). Imported by
seed3.py; used by run(host, cell, "seed3"). The meanings are listed in seed3.py's docstring (one place); this file is the
implementation. Nothing here is tuned per row. A missing hook = the operator is "not bound" for that host (reported).

Shared notation: s = state at the decision; std = host.default(s); a* = the core choice of REAL3 v1 (seed3.step3);
merge(s, {p: a_p, ...}) = one action applying a_p on part p, parts in dict order get the step's resource first, parts not
named take the standard; value v_H(a | plan or policy) = mean objective over the same >= TREE model forks used by seed.py,
H steps ahead (the fork, the forks' randomness and the objective are the host's; identical to seed._rollout).
"""
import copy, hashlib, json, os, pickle
import seed as S

OPS = ("heal", "beam1", "beam3", "contain", "compress", "inherit", "fuse", "carry", "rehost", "pierce", "overlay",
       "enter", "zoom")                                   # candidate operators (valued in the forks under the budget)
ROUTING = ("colour", "rooms", "transplant")               # operators that route / order the others (no own candidate)
COMMON = {"present": "present", "past": "past", "future": "future", "landing": "land", "focus": "beam",
          "P1": "heal", "P2": "contain", "P3": "heal", "P4": "fuse", "P5": "inherit", "P6": "inherit", "P7": "explore",
          "P8": "vote", "P4P5": "fuse"}                   # host families -> common operator names (host.op_of extends)
for _o in OPS: COMMON[_o] = "beam" if _o.startswith("beam") else _o

OPOOL = {}      # TRANSPLANT: common operator name -> [[predicted adv, realised adv], ...] (shared by all rows; persisted)
SHAPES = {}     # COMPRESS: shape key (str) -> {"op|rank": [confirmed, contradicted]} (persisted)
INH = {}        # INHERIT: (host class, shape key) -> {"plan": [actions], "conf": n, "contra": n} (in memory: host actions)
STATS = {"loaded_from": None, "loaded_ops": 0, "saved_to": None, "fallback": 0}


def _load():
    p = os.environ.get("SEED3_POOL_IN")
    if not p or not os.path.exists(p): return
    with open(p) as f: d = json.load(f)
    for k, v in d.get("ops", {}).items(): OPOOL.setdefault(k, []).extend([list(x) for x in v])
    for k, v in d.get("shapes", {}).items():
        for e, cc in v.items():
            cur = SHAPES.setdefault(k, {}).setdefault(e, [0, 0]); cur[0] += cc[0]; cur[1] += cc[1]
    STATS["loaded_from"] = p; STATS["loaded_ops"] = sum(len(v) for v in d.get("ops", {}).values())


def save():
    p = os.environ.get("SEED3_POOL_OUT")
    if not p: return None
    with open(p, "w") as f:
        json.dump({"ops": {k: v[-200:] for k, v in OPOOL.items()}, "shapes": SHAPES}, f, sort_keys=True)
    STATS["saved_to"] = p; return p


_load()


# ---------------------------------------------------------------- values (tuples: lexicographic rows stay lexicographic)
def T(v): return v if isinstance(v, tuple) else (v,)
def vsub(a, b): return tuple(x - y for x, y in zip(T(a), T(b)))
def vdiv(a, c): return tuple(x / c for x in T(a))
def nonneg(a): return T(a) >= tuple(0.0 for _ in T(a))
def first(a): return T(a)[0]


def akey(x):
    try: return hashlib.md5(pickle.dumps(x, protocol=4)).hexdigest()
    except Exception: return repr(x)


class Ctx:
    """One decision's valuation context: fork-result cache (same action, plan, horizon, policy -> same value; never
    recomputed within the step) and a rollout counter (the compute budget)."""
    def __init__(self, host, s): self.h, self.s, self.cache, self.n = host, s, {}, 0

    def roll(self, a, plan=None, H=None, policy=None, pname=None):
        h = self.h; H = h.horizon if H is None else H
        k = (akey(a), akey(plan) if plan is not None else None, H, pname)
        if k in self.cache: return self.cache[k]
        self.n += 1; vals = []; taken0 = []
        for j in range(max(S.TREE, getattr(h, "samples", 1))):
            f = h.fork(self.s, j); f = h.step(f, h.valid(f, a)); taken = []; t = 0
            while not h.done(f) and t < H:
                b = None
                if policy is not None:
                    try: b = policy(f, t)
                    except (KeyError, AttributeError, TypeError, IndexError, ValueError): b = None; STATS["fallback"] += 1
                if b is None: b = plan[t] if (plan is not None and t < len(plan)) else h.default(f)
                b = h.valid(f, b); taken.append(b); f = h.step(f, b); t += 1
            vals.append(T(h.objective(f)))
            if j == 0: taken0 = taken
        m = tuple(sum(v[i] for v in vals) / len(vals) for i in range(len(vals[0])))
        self.cache[k] = (m, taken0, vals); return self.cache[k]


# ---------------------------------------------------------------- binding check
def binding(host):
    has = lambda n: hasattr(host, n)
    P = has("parts") and has("merge"); po = has("part_objective")
    def b(ok, why): return "bound" if ok else "not bound: " + why
    sub = False
    if P:
        try: sub = True if callable(getattr(host, "parts")) and host.parts.__code__.co_argcount >= 3 else False
        except AttributeError: sub = False
    return {
        "heal": b(P and po, "needs parts+merge+part_objective (worst part)"),
        "beam1": b(P and has("focus"), "needs parts+merge+focus"),
        "beam3": b(P and has("focus"), "needs parts+merge+focus"),
        "contain": b(P and po, "needs parts+merge+part_objective (colour: failing part)"),
        "compress": b(has("shape") or (P and po), "needs shape or parts+part_objective"),
        "inherit": b(has("shape") or (P and po), "needs shape or parts+part_objective"),
        "fuse": b(P or has("joint"), "needs parts+merge or joint"),
        "carry": b(has("carry"), "needs carry"),
        "rehost": b(P and has("map_part"), "needs parts+merge+map_part"),
        "pierce": b(P, "needs parts+merge"),
        "overlay": b(P, "needs parts+merge"),
        "enter": ("bound (depth 2)" if sub else "bound (depth 1: parts(state, within) not offered)") if P
                 else "not bound: needs parts+merge",
        "zoom": "bound (generic)",
        "colour": b(P and po, "needs parts+part_objective"),
        "rooms": "bound (generic)",
        "transplant": "bound (generic; file: SEED3_POOL_IN / SEED3_POOL_OUT)",
    }


def op_of(host, fam):
    base = fam.split("+")[0]
    if hasattr(host, "op_of"):
        o = host.op_of(base)
        if o: return o
    if base.startswith("F:"): return "frame"
    return COMMON.get(base, COMMON.get(base.rstrip("0123456789"), base))


def score(op):   # P6 on the shared pool: realised advantage of the last 10 uses (any row)
    return sum(r for _, r in OPOOL.get(op, [])[-10:])


# ---------------------------------------------------------------- the per-run operator state
class Run:
    def __init__(self, host):
        self.host = host; self.bound = binding(host); self.prev_po = None; self.colour = {}
        self.used = {o: 0 for o in OPS + ROUTING}; self.tried = {o: 0 for o in OPS}
        self.rooms = {"Eagle": 0, "Owl": 0, "Associated": 0, "base": 0}
        self.colour_counts = {"failing": 0, "recovering": 0, "healthy": 0}
        self.v1_roll = 0; self.extra_roll = 0; self.steps = 0; self.enter_depth = {1: 0, 2: 0}
        self.hname = type(host).__name__; self.zoom_scale = {}; self.v1_roll_step = 0; self._last_shape = None; self.vetoed = 0; self.passed = {o: 0 for o in OPS}

    def ok(self, op): return self.bound[op].startswith("bound")

    # ---- COLOUR: per-part tag from the trace of part objectives
    def paint(self, s):
        if not self.ok("colour"): return {}
        h = self.host; ps = list(h.parts(s)); po = {p: float(first(h.part_objective(s, p))) for p in ps}
        mean = sum(po.values()) / max(1, len(po)); col = {}
        for p in ps:
            d = po[p] - (self.prev_po or {}).get(p, po[p])
            col[p] = "failing" if (d < 0 and po[p] < mean) else ("recovering" if (d > 0 and po[p] < mean) else "healthy")
            self.colour_counts[col[p]] += 1
        self.prev_po = po; self.colour = col; self.used["colour"] += 1; return col

    def shape(self, s):
        h = self.host
        if hasattr(h, "shape"): return str(h.shape(s))
        if not (self.ok("colour")): return None
        ps = list(h.parts(s)); po = [float(first(h.part_objective(s, p))) for p in ps]
        order = tuple(sorted(range(len(ps)), key=lambda i: po[i]))     # rank pattern of the parts
        spread = round(max(po) - min(po), 1) if po else 0.0
        return str((order, spread, tuple(self.colour.get(p, "healthy")[0] for p in ps)))


# ---------------------------------------------------------------- one decision
def decide(R, s, core, log, ctx, own):
    """core = (a*, fam, key, taken, v, v_present) from seed3.step3; log = [(v, fam, name, cn, a, taken)] v1 valued.
    Returns (action, op or None, key, plan, v_pred, v_present, info)."""
    h = R.host; a_core, fam_core, key_core, taken_core, v_core, v_pres = core
    present = h.valid(s, h.default(s))
    v_std = ctx.roll(present)[0]                                         # the membrane bound (standard, H)
    col = R.paint(s)
    ps = list(h.parts(s)) if R.ok("pierce") else []
    po = {p: float(first(h.part_objective(s, p))) for p in ps} if ps and hasattr(h, "part_objective") else {}
    # second-best v1 candidate (a different action): OVERLAY's partner and FUSE's pool
    seen = {akey(h.valid(s, a_core))}; tops = [h.valid(s, a_core)]
    for v, fam, name, cn, a, tk in sorted(log, key=lambda x: T(x[0]), reverse=True):
        k = akey(a)
        if k not in seen: seen.add(k); tops.append(a)
        if len(tops) >= 3: break
    pvc = {}
    def pv(a):                                   # per-part value of a applied on one part only (standard elsewhere)
        k = akey(a)
        if k not in pvc: pvc[k] = {p: ctx.roll(h.valid(s, h.merge(s, {p: a})))[0] for p in ps}
        return pvc[k]
    def gain(a, p): return vsub(pv(a)[p], v_std)
    def bottleneck(): return max(ps, key=lambda p: T(gain(tops[0], p)))
    def worst():
        fail = [p for p in ps if col.get(p) == "failing"]
        pool = fail or ps
        return min(pool, key=lambda p: po.get(p, 0.0))
    def mk(a, plan=None, policy=None, pname=None): return (h.valid(s, a), plan, policy, pname)

    # -------- builders: op -> (action, plan, policy, pname) or None (not applicable in this state: route by state)
    def b_heal():
        w = worst(); a = h.focus(s, w) if hasattr(h, "focus") else a_core
        return mk(h.merge(s, {w: a}))
    def b_beam(k):
        p = bottleneck() if pvc else (worst() if po else ps[0])
        pol = (lambda f, t: h.focus(f, p) if t < k - 1 else None) if k > 1 else None
        return mk(h.focus(s, p), policy=pol, pname=f"beam{k}:{akey(p)}" if k > 1 else None)
    def b_contain():
        fail = [p for p in ps if col.get(p) == "failing"]
        if not fail: return None                                         # nothing is failing: CONTAIN not routed
        f = min(fail, key=lambda p: po.get(p, 0.0))
        d = {p: a_core for p in ps if p != f}; d[f] = present
        return mk(h.merge(s, d))
    def b_fuse():
        if ps:
            d = {}
            for p in sorted(ps, key=lambda p: T(max((gain(a, p) for a in tops), key=T)), reverse=True):
                d[p] = max(tops, key=lambda a: T(pv(a)[p]))
            return mk(h.merge(s, d))
        return None
    def b_joint():
        return [mk(a) for _, a in h.joint(s)] if hasattr(h, "joint") else []
    def b_overlay():
        if len(tops) < 2: return None
        a1, a2 = tops[0], tops[1]; d = {}
        for p in sorted(ps, key=lambda p: T(max(gain(a1, p), gain(a2, p), key=T)), reverse=True):
            d[p] = a1 if T(pv(a1)[p]) >= T(pv(a2)[p]) else a2
        return mk(h.merge(s, d), plan=taken_core or None)
    def b_pierce():
        return mk(h.merge(s, {bottleneck(): a_core}))
    def b_rehost():
        pf = bottleneck(); pt = worst() if po else min(ps, key=lambda p: T(gain(tops[0], p)))
        if pt == pf: return None
        return mk(h.merge(s, {pf: a_core, pt: h.map_part(s, a_core, pf, pt)}))
    def b_carry():
        return mk(h.carry(s, a_core))
    def b_enter():
        p = bottleneck(); inside = list(tops) + ([h.focus(s, p)] if hasattr(h, "focus") else [])
        rest = {q: a_core for q in ps if q != p}
        best = max(inside, key=lambda c: T(ctx.roll(h.valid(s, h.merge(s, {p: c, **rest})))[0]))
        act = h.valid(s, h.merge(s, {p: best, **rest})); R.enter_depth[1] += 1
        if R.bound["enter"] == "bound (depth 2)":                       # the quark of the quark: choose inside p again
            subs = list(h.parts(s, p)) or []
            for q in subs:
                for c in inside:
                    cand = h.valid(s, h.merge(s, {q: c, p: best, **rest}))
                    if T(ctx.roll(cand)[0]) > T(ctx.roll(act)[0]): act = cand
            if subs: R.enter_depth[2] += 1
        return mk(act)
    def b_zoom():                                                        # block: the same action held 3 steps
        return mk(a_core, policy=lambda f, t: a_core if t < 2 else None, pname="zoomblock")
    sh = R.shape(s) if (R.ok("compress") or R.ok("inherit")) else None
    R._last_shape = sh
    def b_inherit():
        e = INH.get((R.hname, sh))
        if not e: return None
        return mk(e["plan"][0], plan=e["plan"][1:] or None)
    BUILD = {"heal": b_heal, "beam1": lambda: b_beam(1), "beam3": lambda: b_beam(3), "contain": b_contain,
             "fuse": b_fuse, "overlay": b_overlay, "pierce": b_pierce, "rehost": b_rehost, "carry": b_carry,
             "enter": b_enter, "zoom": b_zoom, "inherit": b_inherit}
    def b_compress():
        ent = SHAPES.get(sh) if sh is not None else None
        if not ent: return None
        e = max(ent.items(), key=lambda kv: kv[1][0] - kv[1][1])
        if e[1][0] <= e[1][1]: return None
        op = e[0]
        if op == "core": return mk(a_core)   # stored: the core choice served here; the hologram replays it
        if op in BUILD and op not in ("compress",) and R.ok(op): return BUILD[op]()
        return None
    BUILD["compress"] = b_compress

    # -------- ROOMS (route by state)
    m_std, _, vals_std = ctx.roll(present); m_core, _, vals_core = ctx.roll(h.valid(s, a_core), taken_core or None)
    dis = sum(1 for x, y in zip(vals_core, vals_std) if (first(x) - first(y)) * (first(m_core) - first(m_std)) < 0)
    # near the end (25 Nov 02:25 fix, before any REAL3 seal): the REAL episode has fewer steps left than the horizon
    # (host.remaining(s) if given); else the forks end within 2 steps. Forks that end early only because a sub-unit
    # (one task, one turn) ends do not make every step "Associated" any more.
    rem = h.remaining(s) if hasattr(h, "remaining") else None
    near_end = (rem < h.horizon) if rem is not None else len(ctx.roll(present)[1]) <= 2
    conf = any(len(OPOOL.get(o, [])) >= 3 and all(r > 0 for _, r in OPOOL[o][-3:]) for o in set(COMMON[x] for x in OPS))
    room = ("Associated" if near_end else "Eagle" if dis >= 0.25 * len(vals_std) else "Owl" if conf else "base")
    R.rooms[room] += 1; R.used["rooms"] += 1

    # -------- budget: top-N by shared pool score (P6, TRANSPLANT) + one untried operator (P7); <= ~3x the v1 step
    avail = [o for o in OPS if R.ok(o)]
    order = sorted(avail, key=lambda o: -score(COMMON[o]))
    explore = min(avail, key=lambda o: (R.tried[o], OPS.index(o))) if avail else None
    must = [o for o in (order[:1] + ([explore] if explore else [])) if o]
    budget = max(4, 2 * R.v1_roll_step) if room != "Owl" else max(2, R.v1_roll_step)
    if any(OPOOL.get(COMMON[o]) for o in avail): R.used["transplant"] += 1
    best = None; valued = []
    queue = list(dict.fromkeys(must + order)); done_ops = []
    for o in queue:
        if o not in must and ctx.n >= budget: break
        R.tried[o] += 1; done_ops.append(o)
        try:
            built = BUILD[o]() if o != "fuse" else None
            cands = [built] if built is not None else []
            if o == "fuse": cands = ([b_fuse()] if ps else []) + b_joint(); cands = [c for c in cands if c]
        except (KeyError, AttributeError, TypeError, IndexError, ValueError):
            STATS["fallback"] += 1; cands = []
        for a, plan, pol, pname in cands:
            m, tk, _ = ctx.roll(a, plan, policy=pol, pname=pname)
            if not nonneg(vsub(m, v_std)):                                         # G: Law 0 membrane
                if o == "inherit" and (R.hname, sh) in INH: INH[(R.hname, sh)]["contra"] += 1   # forks contradict it
                continue
            valued.append((m, o, a, plan, pol, pname, tk)); R.passed[o] += 1
            if best is None or T(m) > T(best[0]): best = (m, o, a, plan, pol, pname, tk)
        if room == "Owl" and best is not None and T(best[0]) > T(v_core) and o not in must: break
    R.extra_roll += ctx.n
    info = {"room": room, "op": None}
    if best is None: return a_core, None, key_core, taken_core, v_core, v_pres, info
    m, o, a, plan, pol, pname, tk = best
    # -------- comparison op vs core: in the room's horizon (Eagle 2H, Associated 1, else H); ZOOM: across scales
    H = h.horizon
    def at(a_, plan_, pol_, pname_, Hs): return ctx.roll(a_, plan_, H=Hs, policy=pol_, pname=pname_)[0]
    core_args = (h.valid(s, a_core), taken_core or None, None, None)
    if "zoom" in done_ops:                     # ZOOM valued this step: the choice is made across time scales
        best_sc = None
        for Hs in sorted({max(1, H // 2), H, 2 * H}):
            vc = at(*core_args, Hs); vo = at(a, plan, pol, pname, Hs); vs = at(present, None, None, None, Hs)
            for who, vv in (("core", vc), ("op", vo)):
                adv = vdiv(vsub(vv, vs), Hs)
                if nonneg(adv) and (best_sc is None or T(adv) > T(best_sc[0])): best_sc = (adv, who, Hs)
        take = best_sc is not None and best_sc[1] == "op"; R.zoom_scale[best_sc[2] if best_sc else 0] = \
            R.zoom_scale.get(best_sc[2] if best_sc else 0, 0) + 1
    else:
        Hs = {"Eagle": 2 * H, "Associated": 1}.get(room, H)
        take = T(at(a, plan, pol, pname, Hs)) > T(at(*core_args, Hs)) if Hs != H else T(m) > T(v_core)
        if room == "Associated": take = take and nonneg(vsub(m, at(*core_args, H)))   # local, never worse at H
    # P8 VOTE OF FUTURES (v2 rev 1, after the first toy dev run): an operator replaces a* only if it is at least as good
    # as a* in a majority of the same forks at H (guards against picking fork noise among many candidates)
    if take:
        vo = ctx.roll(a, plan, policy=pol, pname=pname)[2]; vc = ctx.roll(*core_args[:2])[2]
        take = sum(1 for x, y in zip(vo, vc) if T(x) >= T(y)) * 2 > len(vo)
        if not take: R.vetoed += 1
    if not take: return a_core, None, key_core, taken_core, v_core, v_pres, info
    info["op"] = o; R.used[o] += 1
    return a, o, f"op:{o}|{room}", (tk if plan is None else list(plan)), m, v_std, info


def record(R, s_dec, op, fam_core, realised_adv, pred_adv, own, a):
    """O: after the real step. TRANSPLANT pool (common names), COMPRESS (shape -> op|rank), INHERIT (shape -> plan)."""
    name = COMMON[op] if op else op_of(R.host, fam_core)
    if name != "present":
        OPOOL.setdefault(name, []).append([float(pred_adv), float(realised_adv)])
    sh = R._last_shape
    if sh is None: return
    tag = op if op else "core"
    e = SHAPES.setdefault(sh, {}).setdefault(tag, [0, 0]); e[0 if realised_adv > 0 else 1] += 1
    if R.ok("inherit"):
        k = (R.hname, sh)
        if op == "inherit" and k in INH:
            INH[k]["conf" if realised_adv > 0 else "contra"] += 1
            if INH[k]["contra"] > INH[k]["conf"]: del INH[k]                          # contradicted more than confirmed
        elif realised_adv > 0 and k not in INH:
            INH[k] = {"plan": [copy.deepcopy(a)] + [copy.deepcopy(x) for x in (own or [])], "conf": 0, "contra": 0}
