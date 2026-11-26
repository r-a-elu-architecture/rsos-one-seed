# RSOS R3 programs, domain 4: an Earth-observation satellite downlinking over ground-station passes.
# Host = computer: VAKOG order V -> A -> K -> O -> G (U157).
#   V (see)    : every item on board against every known pass: can it still arrive before its deadline in this
#                pass, in a later pass, in none (Law 1: only size, value, deadline and the pass table are read).
#   A (choose) : the room by state:
#                deficit  : everything deliverable fits in this pass (the lack is capacity unused) -> send all
#                overload : the urgent items (no later pass can deliver them) exceed this pass -> urgent by value
#                stable   : otherwise -> the plan over the known passes, then pull forward
#   K (act)    : the plan: each item placed in the LATEST pass that can still deliver it (Law 4: land now only what
#                changes the future: what cannot wait); this pass is then filled with the most valuable per MB of
#                the rest (nothing wasted); the order inside the pass is earliest deadline first (every last byte
#                before its deadline); the tail is filled with a FRAGMENT of the item whose rest still lands later
#                (green particle at the place of need, U102/U167; Law 6 graceful use of capacity).
#   O (trace)  : the fragment's rest is carried to the later pass (carry; inherit the partial item).
#   G (result) : total value delivered before deadlines.
# Laws: Law 0 (each program checks its own order: the EDF feasibility check drops any item that would miss its
# deadline, so nothing is sent that cannot count), Law 1, Law 2 (the program sends ids only; the runtime packs and
# computes the bytes), Law 3 (tiger_edf: repair only the part of the standard that differs: its order and its tail),
# Law 4 (withhold what can wait when the pass is contested), Law 5 (the known pass table is used: what a later pass
# can deliver is not taken now from items that cannot wait), Law 6 (fragment: graceful filling of the tail).

RATE = 7200.0          # MB per hour (2 MB/s)
FRAG = 1000000000


def _pass(p):
    return float(p[0]), float(p[1]), float(p[2])


def _density(it):
    s = float(it.get("size") or 0) or 1e-9
    return float(it.get("value") or 0) / s


def _fits_alone(it, p):
    s, e, c = _pass(p)
    size = float(it["size"])
    start = max(s, float(it.get("arr", s)))
    return size <= c and start + size / RATE <= float(it["deadline"])


def _edf_ok(items, p):
    # Law 0 self-check: in deadline order every last byte arrives before its deadline and the total fits
    s, e, c = _pass(p)
    used = 0.0
    for it in sorted(items, key=lambda x: (float(x["deadline"]), int(x["id"]))):
        used += float(it["size"])
        if used > c + 1e-9 or s + used / RATE > float(it["deadline"]) + 1e-12:
            return False
    return True


def _see(st):
    passes = list(st.get("passes") or [])
    t = int(st.get("t", 0) or 0)
    queue = [it for it in (st.get("queue") or []) if float(it.get("size") or 0) > 0]
    if t >= len(passes) or not queue:
        return None
    cur = passes[t]
    later = list(range(t + 1, len(passes)))
    now_ok = [it for it in queue if _fits_alone(it, cur)]
    later_ok = {it["id"]: [k for k in later if _fits_alone(it, passes[k])] for it in queue}
    urgent = [it for it in now_ok if not later_ok[it["id"]]]
    return {"passes": passes, "t": t, "cur": cur, "queue": queue, "now_ok": now_ok, "later_ok": later_ok,
            "urgent": urgent, "later": later}


def _greedy(items, p, key):
    chosen = []
    for it in sorted(items, key=key):
        if _edf_ok(chosen + [it], p):
            chosen.append(it)
    return chosen


def _plan_now(v):
    # K: plan over the known passes: latest deliverable pass first; this pass keeps what cannot wait
    passes, t = v["passes"], v["t"]
    used = {k: 0.0 for k in range(t, len(passes))}
    now = []
    for it in sorted(v["queue"], key=lambda x: (-_density(x), float(x["deadline"]), int(x["id"]))):
        size, dl = float(it["size"]), float(it["deadline"])
        placed = False
        for k in reversed(v["later_ok"][it["id"]]):
            s, e, c = _pass(passes[k])
            if used[k] + size <= c and s + (used[k] + size) / RATE <= dl:
                used[k] += size
                placed = True
                break
        if not placed and it in v["now_ok"] and _edf_ok(now + [it], v["cur"]):
            now.append(it)
    # pull forward: fill the rest of this pass with the most valuable per MB (no capacity left idle)
    rest = [it for it in v["now_ok"] if it not in now]
    for it in sorted(rest, key=lambda x: (-_density(x), float(x["deadline"]), int(x["id"]))):
        if _edf_ok(now + [it], v["cur"]):
            now.append(it)
    return now


def _fragment(v, chosen):
    # O / carry: the tail gets a fragment of the most valuable item whose rest still lands in a later pass
    s, e, c = _pass(v["cur"])
    left = c - sum(float(it["size"]) for it in chosen)
    if left <= 1.0:
        return None
    ids = {it["id"] for it in chosen}
    best = None
    for it in v["queue"]:
        if it["id"] in ids or float(it["size"]) <= left:
            continue
        rest = float(it["size"]) - left
        ok = False
        for k in v["later"]:
            ps, pe, pc = _pass(v["passes"][k])
            if rest <= pc and ps + rest / RATE <= float(it["deadline"]):
                ok = True
                break
        if ok:
            key = (_density(it), float(it.get("value") or 0))
            if best is None or key > best[0]:
                best = (key, it)
    return None if best is None else FRAG + int(best[1]["id"])


def _out(chosen, frag):
    ids = [int(it["id"]) for it in sorted(chosen, key=lambda x: (float(x["deadline"]), int(x["id"])))]
    if frag is not None:
        ids.append(frag)
    return ids


def _room(v):
    cap = _pass(v["cur"])[2]
    if sum(float(it["size"]) for it in v["now_ok"]) <= cap and _edf_ok(v["now_ok"], v["cur"]):
        return "deficit"
    if sum(float(it["size"]) for it in v["urgent"]) > cap:
        return "overload"
    return "stable"


# Program 1: dragon_plan_house
# Rooms: deficit (all deliverable items fit this pass) -> send all, EDF order, fragment tail ·
#        overload (urgent items exceed the pass) -> urgent by value per MB, then the rest, EDF, fragment ·
#        stable -> the plan over the known passes (latest deliverable pass) + pull forward, EDF, fragment.
# Chain: V deliverability per pass -> A room -> K PLAN (Law 4 withholding of what can wait) -> FILL -> ORDER(EDF)
#        -> O FRAGMENT/carry -> G.
# Laws: 0 (EDF self-check), 1, 2, 4, 5, 6.
# Invariant: every listed whole item meets its deadline in the listed order · check: _edf_ok(chosen) before landing.
def dragon_plan_house(st):
    v = _see(st)
    if v is None:
        return None
    room = _room(v)
    if room == "deficit":
        chosen = list(v["now_ok"])
    elif room == "overload":
        chosen = _greedy(v["urgent"], v["cur"], lambda x: (-_density(x), float(x["deadline"]), int(x["id"])))
        rest = [it for it in v["now_ok"] if it not in chosen]
        for it in sorted(rest, key=lambda x: (-_density(x), int(x["id"]))):
            if _edf_ok(chosen + [it], v["cur"]):
                chosen.append(it)
    else:
        chosen = _plan_now(v)
    if not _edf_ok(chosen, v["cur"]):
        return None
    return _out(chosen, _fragment(v, chosen))


# Program 2: dragon_plan_nofrag
# The same house without the fragment (the tail is left to the standard): rooms and chain as dragon_plan_house
# without O/carry.  Laws: 0, 1, 2, 4, 5.  Invariant / check: as Program 1.
def dragon_plan_nofrag(st):
    v = _see(st)
    if v is None:
        return None
    room = _room(v)
    if room == "deficit":
        chosen = list(v["now_ok"])
    elif room == "overload":
        chosen = _greedy(v["urgent"], v["cur"], lambda x: (-_density(x), float(x["deadline"]), int(x["id"])))
        rest = [it for it in v["now_ok"] if it not in chosen]
        for it in sorted(rest, key=lambda x: (-_density(x), int(x["id"]))):
            if _edf_ok(chosen + [it], v["cur"]):
                chosen.append(it)
    else:
        chosen = _plan_now(v)
    if not _edf_ok(chosen, v["cur"]):
        return None
    return _out(chosen, None)


# Program 3: tiger_edf
# White Dragon P3 (Law 3: repair only the part that differs): the standard's own choice (value per MB), but every
# item admitted only if the EDF order still delivers all, the order set to earliest deadline first, and the tail
# filled with a fragment.  Rooms: one (stable).  Chain: V -> K SELECT(density) -> CHECK(EDF) -> ORDER -> O FRAGMENT -> G.
# Laws: 0, 3, 6.  Invariant: same selection rule as the standard · check: _edf_ok(chosen).
def tiger_edf(st):
    v = _see(st)
    if v is None:
        return None
    chosen = _greedy(v["now_ok"], v["cur"], lambda x: (-_density(x), float(x["deadline"]), int(x["id"])))
    return _out(chosen, _fragment(v, chosen))


# Program 4: lion_urgent_value
# Lion (U104, boldest path): items that cannot wait first, ranked by their whole value (not per MB), then the rest by
# value per MB; EDF order; fragment tail.  Rooms: urgent present -> urgent first; none -> density.
# Chain: V urgency -> A -> K SELECT(urgent by value) -> FILL(density) -> ORDER(EDF) -> O FRAGMENT -> G.
# Laws: 0, 4, 6.  Invariant: an urgent item is never displaced by one that can wait · check: urgent admitted first.
def lion_urgent_value(st):
    v = _see(st)
    if v is None:
        return None
    chosen = _greedy(v["urgent"], v["cur"], lambda x: (-float(x.get("value") or 0), float(x["deadline"]), int(x["id"])))
    rest = [it for it in v["now_ok"] if it not in chosen]
    for it in sorted(rest, key=lambda x: (-_density(x), int(x["id"]))):
        if _edf_ok(chosen + [it], v["cur"]):
            chosen.append(it)
    return _out(chosen, _fragment(v, chosen))


MOVES = {
    "dragon_plan_house": dragon_plan_house,
    "dragon_plan_nofrag": dragon_plan_nofrag,
    "tiger_edf": tiger_edf,
    "lion_urgent_value": lion_urgent_value,
}
