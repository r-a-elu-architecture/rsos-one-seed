"""REAL3 SEED: the map's full seed composed once (owner 24 Nov 20:12-20:29; map Parts 0, H, I, J, K; SEED_V3).
Layer 2 builds the frame, layer 1 is where it lands. One file, one hash; every row binds to it. Nothing tuned per row.

VAKOG ORDER (U157: the order is the program), every step:
  V  see       host.observe(state) is read (optional); the trace of what landed before is read
  A  choose    candidates = present + host branches + LIBRARY PRIMITIVES bound by the host (Part I.2: P1 counter-shift,
               P2 price on harm, P3 part repair, P4 joint choice, P5 value carried back, P6 reinforce what worked,
               P7 explore then settle, P8 vote of futures) + the host's FRAME levers (layer-2 moves the standard frame
               does not use: blind plans, hologram messages, joint measurement, shared pools...) + own past / own plan;
               each valued in the unit's own future on the real tree (seed._rollout, >= TREE model futures, never
               the real future); candidates disabled by the observer (apoptosis) are skipped
  K  act       the chosen action LANDS: per part (Law 1, seed.land: withhold / retarget by need) when the host's parts
               are independent, as a WHOLE (hologram, Law 2: no per-part split) when host.coupled(state) says the parts
               drive each other; the observer may switch landing off where its own trace shows it costs
  O  trace     every family's predicted advantage over the present action is recorded with its realised advantage
               (the next step's objective change vs the present-action forecast); the trace is a POOL shared by every
               host and cell in the process (spheres and tubes, U166): what one host learns about a family, all reuse
  G  result    Law 0 membrane on the chosen action (never worse than the standard action in the same futures)
OBSERVER OF THE OBSERVER (U150): a family whose realised advantage is negative in its last 3 uses while predicted
positive is disabled for 5 steps (apoptosis, P7 settle); families with positive realised advantage are tried first (P6).

HOST INTERFACE ADDED (optional, all default to none): primitives(state) -> [(family, name, action)], frame(state) ->
[(family, name, action)], coupled(state) -> bool, observe(state) -> any. Everything else as seed.py.
Modes: run(host, cell, "seed3") ; the other modes stay in seed.py (seed, seed_noland, rollout, default).

REAL3 v2 (owner 25 Nov 00:13, "go"): ALL RSOS operators are SEED OPERATORS, each with one computational meaning valid in
every row, bound through a few optional hooks (real/HOST_INTERFACE_REAL3v2.md; implementation real/seed3_ops.py).
run(host, cell, "seed3") = v2: the v1 choice above (a*, unchanged) is computed first, then the operators below are
valued in the same model forks and replace a* only if strictly better in the room's comparison AND never worse than the
standard action at H (Law 0). run(host, cell, "seed3v1") = REAL3 v1 exactly (kept for comparison).
OPTIONAL HOOKS (each missing hook = the operators that need it are "not bound" for that host; reported, never forced):
  parts(s[, within]) -> [part ids] (within = a part: its sub-parts, for ENTER depth 2)
  merge(s, {p: a_p}) -> action    a_p applied on part p only; dict order = who gets the step's resource first; parts not
                                  named take the standard action (so merge(s, {p: a}) = "a only on p, standard elsewhere")
  part_action(s, a, p) -> action  optional; default merge(s, {p: a})
  part_objective(s, p) -> number  the part's own value now (higher = better)
  focus(s, p) -> action           the whole step's resource on part p
  shape(s) -> hashable            compact state key (default: rank pattern + spread + colours of the part objectives)
  joint(s) -> [(name, action)]    native joint actions (FUSE)
  carry(s, a) -> action           a, with the step's unused resource carried to the next step
  map_part(s, a, p_from, p_to)    a's pattern on p_from re-expressed on p_to (RE-HOST)
  op_of(family) -> name or None   the host's families -> common operator names (TRANSPLANT table)
OPERATORS (meaning; hook):
  COLOUR     each part tagged per step from the trace of its part objective: failing (fell, below the mean), recovering
             (rose, below the mean), healthy; routes HEAL / CONTAIN / BEAM targets. [parts, part_objective]
  HEAL       the worst part (failing first, then lowest part objective) is served FIRST: merge({w: focus(w)}) (a* on w
             if no focus), the rest of the resource standard. [parts, merge, part_objective; focus optional]
  BEAM k     the whole step's resource on one target part for k steps, k in {1, 3} (k=3 valued as a 3-step policy in
             the forks); target = the bottleneck (PIERCE's part) when probed, else the worst part. [parts, merge, focus]
  CONTAIN    the failing part is kept at the standard and served LAST while every other part takes a*; routed only when a
             part is failing. [parts, merge, part_objective]
  COMPRESS   hologram key shape(s); after each real step the operator used (or "core") is stored under the decision's
             shape with confirmed / contradicted counts; at a shape seen before, the stored operator with more
             confirmations than contradictions is re-built at the present state (one lookup, no search). [shape or
             parts+part_objective]
  INHERIT    a plan (action + own continuation) that realised a positive advantage is stored under shape(s); at the same
             shape it is a candidate valued with one rollout (no search); removed when contradicted (realised <= 0 or
             failing the membrane in the forks) more often than confirmed. In memory (actions are host-specific).
             [shape or parts+part_objective]
  FUSE       one joint action serving several parts: per part, the best of the top-3 valued v1 candidates on that part
             (per-part fork values), merged with the largest per-part gain first; plus host.joint(s). [parts+merge or joint]
  CARRY      carry(s, a*): the step's leftover resource carried to the next step. [carry]
  TRANSPLANT the shared pool keyed by COMMON operator names (heal, beam, inherit, fuse, compress, ...; host families
             mapped by COMMON + host.op_of), entries (predicted advantage, realised advantage = real objective after
             the step minus the present action's forecast after one step); orders the operators (P6) for every row;
             loaded at import from env SEED3_POOL_IN, saved at the end of run() to env SEED3_POOL_OUT. [none]
  RE-HOST    a*'s action on its best part (largest per-part gain) mapped onto the worst part and applied on both.
             [parts, merge, map_part]
  PIERCE     straight to the bottleneck: the part where a* alone (standard elsewhere) gains most in the forks; a* is
             applied only there. [parts, merge]
  OVERLAY    per part, the better of the two best v1 candidates (per-part fork values), merged; continuation = a*'s own
             plan. [parts, merge]
  ROOMS      route by state: near the end (the standard fork ends before H) -> Associated (op vs a* compared at H=1);
             forks disagree (>= 25% of forks give a* the opposite sign of its mean advantage) -> Eagle (compared at 2H);
             trace confident (some operator realised > 0 in its last 3 pool uses) -> Owl (operators valued in trace
             order, stop at the first that beats a*, half budget); else base (compared at H). Counts reported. [none]
  ZOOM       time is structure: a* held as a 3-step block is a candidate; when ZOOM is valued in a step, op vs a* is
             decided across scales H/2, H, 2H by the best membrane-safe advantage per step (advantage >= 0 at that
             scale). [none]
  ENTER      the seed's choice run again inside the bottleneck part: candidates = top-3 v1 actions + focus restricted to
             that part, a* elsewhere; depth 2 (when parts(s, within) is offered): the same inside each sub-part; merged
             back. [parts, merge; parts(s, within) for depth 2]
  VOTE (P8)  an operator replaces a* only if it is at least as good as a* in a majority of the same H-step forks; in the
             Associated room it must also be no worse than a* at H (rev 1, after the first toy development run).
  MEMBRANE (Law 0) for every operator: its value at H must be >= the standard action's value at H in the same forks.
COMPUTE BUDGET per step: v1 rollouts n1 (counted); operators add at most max(4, 2*n1) rollouts (Owl: max(2, n1)),
always including the top operator by pool score and the least-tried operator of this run (P7 explore); forks cached
within the step. Not landed again after an operator wins (the operators are themselves per-part landings)."""
import copy, time
import seed as S
import seed3_ops as O

POOL = {}          # spheres and tubes: family -> list of (predicted, realised) advantages, shared across hosts and cells
OFF = {}           # family -> steps left disabled (apoptosis)
POLICY_FALLBACK = [0]   # fork steps where the host's levers were not defined (standard used instead)

def _fam(name):
    return name.split(":")[0] if ":" in name else name.split("-")[0].split("+")[0].split("|")[0]

def _candidates(host, s, past, own):
    present = host.default(s)
    c = [("present", "present", present)]
    for i in (1, 2):
        if len(past) >= i: c.append(("past", f"past-{i}", past[-i]))
        if own and len(own) >= i: c.append(("future", f"future+{i}", own[i - 1]))
    c += [(_fam(n), n, a) for n, a in host.branches(s)]
    if hasattr(host, "primitives"): c += list(host.primitives(s))
    if hasattr(host, "frame"): c += list(host.frame(s))
    c = [x for x in c if OFF.get(x[0], 0) <= 0 or x[0] == "present"]
    score = lambda fam: sum(r for _, r in POOL.get(fam, [])[-10:])
    return sorted(c, key=lambda x: -score(x[0]))          # P6: what worked is tried first (ties keep host order)

def _policy_rollout(host, s, name, fam, first, horizon=None):
    """POLICY CONTINUATION (REAL3 fix, 24 Nov 21:50, before any REAL3 seal): a primitive or frame lever is valued as a
    POLICY, not one step: after `first`, each model fork keeps choosing the candidate with the same name (else the same
    family, else the standard) at every step to the horizon. Same forks, same horizon, same objective as seed._rollout."""
    H = host.horizon if horizon is None else horizon; vals = []; taken0 = []
    for j in range(max(S.TREE, getattr(host, "samples", 1))):
        f = host.fork(s, j); f = host.step(f, host.valid(f, first)); taken = []; h = 0
        while not host.done(f) and h < H:
            try:   # a host whose levers are not defined on its model forks: the fork follows the standard (counted)
                opts = (list(host.primitives(f)) if hasattr(host, "primitives") else []) + \
                       (list(host.frame(f)) if hasattr(host, "frame") else [])
            except (KeyError, AttributeError, TypeError, IndexError):
                opts = []; POLICY_FALLBACK[0] += 1
            a = next((x[2] for x in opts if x[1] == name), None)
            if a is None: a = next((x[2] for x in opts if x[0] == fam), None)
            if a is None: a = host.default(f)
            a = host.valid(f, a); taken.append(a); f = host.step(f, a); h += 1
        vals.append(host.objective(f))
        if j == 0: taken0 = taken
    if isinstance(vals[0], tuple):
        return tuple(sum(v[k] for v in vals) / len(vals) for k in range(len(vals[0]))), taken0
    return sum(vals) / len(vals), taken0

def step3(host, s, past, own, log=None):
    if hasattr(host, "observe"): host.observe(s)                                                  # V
    cand = _candidates(host, s, past, own)                                                         # A
    conts = ([("own", own[1:])] if own else []) + [("standard", None)]
    base = {cn: S._rollout(host, s, cand[0][2] if cand[0][0] == "present" else host.default(s), pl)[0] for cn, pl in conts}
    v_present = max(base.values())
    polfam = {x[0] for x in ((list(host.primitives(s)) if hasattr(host, "primitives") else []) +
                             (list(host.frame(s)) if hasattr(host, "frame") else []))}
    best = None
    for fam, name, a in cand:
        a = host.valid(s, a)
        for cn, pl in conts:
            v, taken = S._rollout(host, s, a, pl)
            if log is not None: log.append((v, fam, name, cn, a, taken))
            if v < base[cn]: continue                                                               # G: Law 0 membrane
            if best is None or v > best[0]: best = (v, fam, name, cn, a, taken)
        if fam in polfam and getattr(host, "policy_cont", True):                                    # A: valued as a policy
            v, taken = _policy_rollout(host, s, name, fam, a)
            if v >= base["standard"] and (best is None or v > best[0]): best = (v, fam, name, "policy", a, taken)
    if best is None:
        a = host.valid(s, host.default(s)); return a, "present", "present|standard", [], v_present, v_present
    v, fam, name, cn, a, taken = best
    coupled = bool(host.coupled(s)) if hasattr(host, "coupled") else False                          # K
    if not coupled and OFF.get("landing", 0) <= 0:
        a2, ev = S.land(host, s, a, taken)
        if ev["withheld"] or ev["retargeted"]:
            v2 = S._rollout(host, s, a2, taken)[0]
            if v2 >= v: a, v, fam = a2, v2, fam + "+landing"
    return a, fam, f"{name}|{cn}", taken, v, v_present

def _adv(x):
    return x[0] if isinstance(x, tuple) else x

def run(host, cell, mode="seed3"):
    """mode "seed3" = REAL3 v2 (v1 choice + seed operators); "seed3v1" = REAL3 v1 exactly."""
    v2 = mode == "seed3"; R = O.Run(host) if v2 else None; t0 = time.time()
    s = host.reset(cell); past, own, trace, pending = [], [], {}, None
    while not host.done(s):
        for k in list(OFF): OFF[k] = max(0, OFF[k] - 1)
        if v2:
            log = []
            a, fam, key, own, v_pred, v_pres = step3(host, s, past, own, log)
            R.v1_roll_step = len(log) + 2                       # v1 rollouts this step (candidates x conts + bases)
            R.v1_roll += R.v1_roll_step
            ctx = O.Ctx(host, s)
            a, op, key, own, v_pred, v_pres, info = O.decide(R, s, (a, fam, key, own, v_pred, v_pres), log, ctx, own)
            f1 = ctx.roll(host.valid(s, host.default(s)), H=0)[0]          # the present action's forecast, one step
            if op: fam = "op:" + op
        else:
            a, fam, key, own, v_pred, v_pres = step3(host, s, past, own)
        trace[key] = trace.get(key, 0) + 1
        before = host.objective(s); past.append(a); s_dec = s; s = host.step(s, a); after = host.objective(s)
        # O: realised advantage of the family = realised one-step change minus the present action's forecast change
        realised = _adv(after) - _adv(before)
        if v2:
            R.steps += 1
            O.record(R, s_dec, op, fam, _adv(after) - O.first(f1), _adv(v_pred) - _adv(v_pres), own, a)
            if op: continue                                       # the v1 family pool is not credited for an operator
        for f in fam.split("+"):
            if f == "present": continue
            POOL.setdefault(f, []).append((_adv(v_pred) - _adv(v_pres), realised))
            last = POOL[f][-3:]
            if len(last) == 3 and all(p > 0 for p, _ in last) and all(r < 0 for _, r in last): OFF[f] = 5   # observer
    out = dict(host.report(s)); out["choices"] = trace
    out["R"] = out["result"] / out["resource"] if out.get("resource") else out["result"]
    out["pool_families"] = {f: len(v) for f, v in POOL.items()}; out["disabled"] = {f: n for f, n in OFF.items() if n}
    out["policy_fallback_steps"] = POLICY_FALLBACK[0]
    if v2:
        out["ops_bound"] = R.bound; out["ops_used"] = {k: v for k, v in R.used.items()}
        out["ops_tried"] = dict(R.tried); out["rooms"] = dict(R.rooms); out["colour_counts"] = dict(R.colour_counts)
        out["zoom_scale_decisions"] = dict(R.zoom_scale); out["enter_depth"] = dict(R.enter_depth)
        out["vote_vetoed"] = R.vetoed; out["ops_passed_membrane"] = dict(R.passed)
        out["rollouts_v1"] = R.v1_roll; out["rollouts_ops"] = R.extra_roll
        out["op_fallback"] = O.STATS["fallback"]; out["pool_loaded_from"] = O.STATS["loaded_from"]
        out["pool_saved"] = O.save(); out["inherit_entries"] = len(O.INH); out["shape_keys"] = len(O.SHAPES)
    out["seconds"] = round(time.time() - t0, 2)
    return out
