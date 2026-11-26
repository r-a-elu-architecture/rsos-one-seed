# RSOS R2 programs, domain 4: an Earth-observation satellite downlinking over ground-station passes.
# Host = computer: V -> A -> K -> O -> G (U157):
#   V (see)     the queue, this pass and the passes ahead (past, present, future: U163)
#   A (choose)  the heard state selects the room: deficit (items whose last chance is now) /
#               overload (queue exceeds the next two passes) / stable
#   K (act)     the ordered list: a feasible set packed by the room's priority, sent in deadline order,
#               the tail landed with a FRAGMENT
#   O (trace)   each item's deadline and its later chances are the trace carried into the next pass
#   G (result)  value delivered before deadlines
# Rate 2 MB/s = 7200 MB per hour. Pure functions of `st`; standard library only.

RATE = 7200.0
FRAG = 1000000000


# ---------------------------------------------------------------- V: see
def _see(st):
    t = int(st.get("t", 0))
    passes = [tuple(p) for p in (st.get("passes") or [])]
    if t >= len(passes):
        return None
    q = [it for it in (st.get("queue") or []) if float(it.get("size", 0)) > 0]
    s0, e0, c0 = passes[t]
    return {"t": t, "passes": passes, "q": q, "start": float(s0), "end": float(e0), "cap": float(c0)}


def _dens(it):
    return float(it["value"]) / max(float(it["size"]), 1e-9)


def _later_ok(v, it, size=None):
    # the item still has a whole chance at a later pass (ignoring contention)
    sz = float(it["size"]) if size is None else size
    for j in range(v["t"] + 1, len(v["passes"])):
        s, e, c = v["passes"][j]
        if s >= float(it["deadline"]):
            break
        if sz <= float(c) and float(s) + sz / RATE < float(it["deadline"]):
            return True
    return False


def _feasible(v, items):
    # EDF order (optimal for feasibility of one channel with common start); cap and deadlines checked
    cum = 0.0
    for it in sorted(items, key=lambda i: (float(i["deadline"]), -_dens(i))):
        cum += float(it["size"])
        if cum > v["cap"] + 1e-9:
            return False
        if v["start"] + cum / RATE >= float(it["deadline"]):
            return False
    return True


def _pack(v, prio):
    # K: greedy in the room's priority, each addition checked as a whole (Law 0: no admitted item loses its deadline)
    sel = []
    for it in prio:
        if _feasible(v, sel + [it]):
            sel.append(it)
    return sorted(sel, key=lambda i: (float(i["deadline"]), -_dens(i)))


def _fragment(v, sel):
    # green particle on the tail (U102/U167): the unused capacity lands on the densest item that cannot fit
    # whole now and can still finish at a later pass before its deadline
    used = sum(float(i["size"]) for i in sel)
    tail = v["cap"] - used
    if tail <= 1.0:
        return None
    ids = set(i["id"] for i in sel)
    end_t = v["start"] + used / RATE
    cands = []
    for it in v["q"]:
        if it["id"] in ids or float(it["size"]) <= tail:
            continue
        rest = float(it["size"]) - tail
        if end_t >= float(it["deadline"]):
            continue
        if _later_ok(v, it, size=rest):
            cands.append(it)
    if not cands:
        return None
    best = max(cands, key=lambda i: (_dens(i), -float(i["deadline"])))
    return FRAG + int(best["id"])


def _out(v, sel):
    ids = [int(i["id"]) for i in sel]
    f = _fragment(v, sel)
    if f is not None:
        ids.append(f)
    return ids


def _std_prio(v):
    return sorted(v["q"], key=lambda i: (-_dens(i), float(i["deadline"])))


def _deficit_prio(v):
    # P1 counter-shift / U103 deficit: items with no later chance are pulled to the front, densest first
    urgent = [i for i in v["q"] if not _later_ok(v, i)]
    rest = [i for i in v["q"] if _later_ok(v, i)]
    return sorted(urgent, key=lambda i: -_dens(i)) + sorted(rest, key=lambda i: -_dens(i))


def _lookahead_prio(v, reserve=0.8):
    # P5 value carried back / future pacing over the known passes: place every item, densest first, in the
    # LATEST pass that can still carry it before its deadline (future capacity kept at `reserve` for arrivals);
    # what lands on THIS pass is what cannot wait. Then the rest, densest first.
    passes = v["passes"]
    t = v["t"]
    horizon = max([float(i["deadline"]) for i in v["q"]] + [v["start"]])
    js = [j for j in range(t, len(passes)) if float(passes[j][0]) < horizon]
    rem = {j: (float(passes[j][2]) if j == t else reserve * float(passes[j][2])) for j in js}
    full = {j: rem[j] for j in js}
    now = []
    for it in sorted(v["q"], key=lambda i: -_dens(i)):
        sz = float(it["size"])
        for j in reversed(js):
            if rem[j] < sz:
                continue
            pos = full[j] - rem[j] + sz
            if float(passes[j][0]) + pos / RATE < float(it["deadline"]):
                rem[j] -= sz
                if j == t:
                    now.append(it)
                break
    ids = set(i["id"] for i in now)
    return now + [i for i in _std_prio(v) if i["id"] not in ids]


def _room(v):
    if not v["q"]:
        return None
    if any(not _later_ok(v, i) and _dens(i) > 0 for i in v["q"]):
        return "deficit"
    nxt = float(v["passes"][v["t"] + 1][2]) if v["t"] + 1 < len(v["passes"]) else 0.0
    if sum(float(i["size"]) for i in v["q"]) > v["cap"] + nxt:
        return "overload"
    return "stable"


# ---------------------------------------------------------------- Program 1
# house_downlink
# Rooms (trigger -> chain):
#   deficit  (an item has no later whole chance)        -> deficit priority (P1 counter-shift, U103) -> pack -> EDF -> fragment
#   overload (queue MB > this pass + next pass)         -> lookahead priority (latest-fit, P5, future pacing) -> pack -> EDF -> fragment
#   stable                                              -> standard priority -> pack -> EDF -> fragment (Law 3: repair only the order)
# Chain: V see queue + passes ahead -> A room -> K pack (each addition checked) -> send in deadline order
#   -> green particle on the tail (fragment) -> O deadlines carried -> G value.
# Laws: Law 4 (land only items whose future needs this pass first), Law 0 (no admitted item misses its deadline:
#   feasibility checked per addition), Law 6 (capacity: graceful fill of the tail by a fragment), Law 3, zoom
#   invariance (the same feasibility rule per item and on the whole pass).
# Invariant + check: the sent set fits the capacity and every item's last byte arrives before its deadline in the
#   sent order (check: _feasible on the final list); the fragment is only an item that can finish later.
def house_downlink(st):
    v = _see(st)
    if v is None:
        return None
    room = _room(v)
    if room is None:
        return None
    if room == "deficit":
        prio = _deficit_prio(v)
    elif room == "overload":
        prio = _lookahead_prio(v)
    else:
        prio = _std_prio(v)
    return _out(v, _pack(v, prio))


# ---------------------------------------------------------------- Program 2
# deficit_land
# Rooms: one room for every state: deficit priority (items whose only chance is now first, densest first),
#   then the rest densest first.
# Chain: V -> K deficit (U103) / counter-shift (P1) -> pack -> EDF -> fragment -> G.
# Laws: Law 4, Law 0, Law 6.
# Invariant + check: as house_downlink.
def deficit_land(st):
    v = _see(st)
    if v is None or not v["q"]:
        return None
    return _out(v, _pack(v, _deficit_prio(v)))


# ---------------------------------------------------------------- Program 3
# lookahead_latest
# Rooms: one room: every item is placed in the latest known pass that still carries it before its deadline
#   (future capacity at 80 % for arrivals); this pass carries what cannot wait, then the densest rest.
# Chain: V past/present/future (U163) -> K future pacing (3 futures -> all passes) + P5 value carried back
#   -> pack -> EDF -> fragment -> G.
# Laws: Law 4 (withholding is a move: what can wait, waits), Law 0, Law 6 (reserve for arrivals).
# Invariant + check: as house_downlink.
def lookahead_latest(st):
    v = _see(st)
    if v is None or not v["q"]:
        return None
    return _out(v, _pack(v, _lookahead_prio(v)))


# ---------------------------------------------------------------- Program 4
# standard_healed
# Rooms: one room: the standard's own priority (value per MB), healed in two places only (White Dragon U90 / P3:
#   repair only the part that differs): (1) the set is packed with a whole-set deadline check and sent in
#   deadline order, (2) the tail is landed with a fragment.
# Chain: V -> K standard priority -> pack -> EDF -> fragment -> G.
# Laws: Law 3 (living structure), Law 0, Law 6.
# Invariant + check: as house_downlink; the set differs from the standard only where the standard would skip
#   an item it could have delivered in another order, or leave the tail empty.
def standard_healed(st):
    v = _see(st)
    if v is None or not v["q"]:
        return None
    return _out(v, _pack(v, _std_prio(v)))


# ---------------------------------------------------------------- Program 5
# house_tiger_lion
# Rooms (route by the class of the deficit):
#   an ALERT has no later chance  -> Tiger (U104, the closest precise path): urgent alerts first, then deficit priority
#   overload                      -> Lion (U104, the boldest path): lookahead with the full future capacity (reserve 1.0)
#   otherwise                     -> deficit priority
#   always: pack -> EDF -> fragment.
# Chain: V -> A (class of need) -> K beam (Tiger | Lion) -> pack -> EDF -> fragment -> O -> G.
# Laws: Law 4, Law 0, Law 6.
# Invariant + check: as house_downlink.
def house_tiger_lion(st):
    v = _see(st)
    if v is None or not v["q"]:
        return None
    urgent_alerts = [i for i in v["q"] if i.get("cls") == "alert" and not _later_ok(v, i)]
    if urgent_alerts:
        first = sorted(urgent_alerts, key=lambda i: (float(i["deadline"]), -_dens(i)))
        ids = set(i["id"] for i in first)
        prio = first + [i for i in _deficit_prio(v) if i["id"] not in ids]
    elif _room(v) == "overload":
        prio = _lookahead_prio(v, reserve=1.0)
    else:
        prio = _deficit_prio(v)
    return _out(v, _pack(v, prio))


MOVES = {
    "house_downlink": house_downlink,
    "deficit_land": deficit_land,
    "lookahead_latest": lookahead_latest,
    "standard_healed": standard_healed,
    "house_tiger_lion": house_tiger_lion,
}
