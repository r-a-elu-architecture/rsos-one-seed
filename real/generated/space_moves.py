"""RSOS operator moves for the Earth-observation downlink host (one decision per ground-station pass).

Each move: st -> ordered list of item ids to send in this pass, or None when the operator does not apply.
Rate 2 MB/s = 7200 MB/h; an item counts only if its last byte lands before its deadline.
"""

RATE = 7200.0  # MB per hour


def _cap(p):
    return min(p[2], (p[1] - p[0]) * RATE)


def _dens(it):
    return it["value"] / max(it["size"], 1e-9)


def _std(items):
    return sorted(items, key=lambda it: -_dens(it))


def _pack(order, p):
    """Greedy pack as the host does: in order, skip items over capacity or late."""
    used, out = 0.0, []
    for it in order:
        if used + it["size"] <= _cap(p) and p[0] + (used + it["size"]) / RATE <= it["deadline"]:
            used += it["size"]
            out.append(it)
    return out


def _now(st):
    p = st["passes"][st["t"]]
    return p, [it for it in st["queue"] if p[0] + it["size"] / RATE <= it["deadline"]]


def _later_passes(st, it):
    """Future passes in which the item could still land if sent first."""
    return [p for p in st["passes"][st["t"] + 1:] if p[0] + it["size"] / RATE <= it["deadline"] and _cap(p) >= it["size"]]


def _ids(items):
    return [it["id"] for it in items] or None


# HEAL: land the particles where the need is: items with no later pass before their deadline go first (by value/MB), then the rest.
def heal(st):
    _, items = _now(st)
    urgent = [it for it in items if not _later_passes(st, it)]
    if not urgent:
        return None
    rest = [it for it in items if it not in urgent]
    return _ids(_std(urgent) + _std(rest))


# CARRY: carry slack to later passes: fewest remaining passes before the deadline first, value/MB within; slack-rich items wait.
def carry(st):
    _, items = _now(st)
    return _ids(sorted(items, key=lambda it: (len(_later_passes(st, it)), -_dens(it))))


# COMPRESS: the whole pass in one choice: 0/1 knapsack of value over pass capacity (10 MB cells), sent earliest deadline first.
def compress(st):
    p, items = _now(st)
    items = [it for it in items if it["size"] <= _cap(p)]
    if not items:
        return None
    W = int(_cap(p) // 10)
    best = {0: (0.0, ())}
    for i, it in enumerate(items):
        w = -(-int(it["size"]) // 10) or 1
        for used, (val, sel) in list(best.items()):
            nu = used + w
            if nu <= W and (nu not in best or best[nu][0] < val + it["value"]):
                best[nu] = (val + it["value"], sel + (i,))
    chosen = [items[i] for i in max(best.values(), key=lambda b: b[0])[1]]
    chosen.sort(key=lambda it: it["deadline"])
    return _ids(_pack(chosen, p))


# PIERCE: pierce into the future passes: simulate the standard on the current queue and pull the items it would lose to the front now.
def pierce(st):
    p, items = _now(st)
    sent = {it["id"] for it in _pack(_std(items), p)}
    left = [it for it in st["queue"] if it["id"] not in sent]
    lost = []
    for q in st["passes"][st["t"] + 1:]:
        left = [it for it in left if q[0] + it["size"] / RATE <= it["deadline"] or lost.append(it)]
        if not left:
            break
        got = {it["id"] for it in _pack(_std(left), q)}
        left = [it for it in left if it["id"] not in got]
    lost += left
    lost_ids = {it["id"] for it in lost}
    front = [it for it in _std(items) if it["id"] in lost_ids]
    if not front:
        return None
    return _ids(front + [it for it in _std(items) if it["id"] not in lost_ids])


# ENTER: inside the pass: the standard's own set, re-ordered earliest deadline first so in-pass deadlines are met.
def enter(st):
    p, items = _now(st)
    chosen = _pack(_std(items), p)
    return _ids(sorted(chosen, key=lambda it: it["deadline"]))


# BEAM: whole pass on one part: the class with the most value deliverable in this pass, by value/MB, then the rest.
def beam(st):
    p, items = _now(st)
    by = {}
    for it in items:
        by.setdefault(it["cls"], []).append(it)
    if len(by) < 2:
        return None
    cls = max(by, key=lambda c: sum(it["value"] for it in _pack(_std(by[c]), p)))
    return _ids(_std(by[cls]) + _std([it for it in items if it["cls"] != cls]))


# CONTAIN: protect the high-value part (Law 0): alerts in deadline order first, then the others by value/MB.
def contain(st):
    _, items = _now(st)
    al = sorted([it for it in items if it["cls"] == "alert"], key=lambda it: it["deadline"])
    if not al:
        return None
    return _ids(al + _std([it for it in items if it["cls"] != "alert"]))


# FUSE: joint choice: the must-go-now items (heal) fused with the knapsack fill of the remaining capacity (compress).
def fuse(st):
    p, items = _now(st)
    urgent = [it for it in items if not _later_passes(st, it)]
    if not urgent:
        return None
    first = _pack(_std(urgent), p)
    used = sum(it["size"] for it in first)
    rest = [it for it in items if it not in first]
    sub = dict(st, queue=rest, passes=list(st["passes"]))
    sub["passes"][st["t"]] = (p[0] + used / RATE, p[1], max(_cap(p) - used, 0.0))
    fill = compress(sub) or []
    by_id = {it["id"]: it for it in rest}
    return _ids(first + [by_id[i] for i in fill if i in by_id])


# ROUTE BY STATE (colour): red = queue over this and the next pass's capacity -> pierce; amber = urgent items -> heal; green -> knapsack.
def route(st):
    p, items = _now(st)
    nxt = st["passes"][st["t"] + 1:st["t"] + 2]
    load = sum(it["size"] for it in items)
    if load > _cap(p) + sum(_cap(q) for q in nxt):
        return pierce(st) or heal(st) or compress(st)
    return heal(st) or compress(st)


# ZOOM: scale H: rank by value per MB divided by the passes left before the deadline (scarcity over the horizon).
def zoom(st):
    _, items = _now(st)
    return _ids(sorted(items, key=lambda it: -_dens(it) / (1 + len(_later_passes(st, it)))))


MOVES = {
    "heal": heal,
    "carry": carry,
    "compress": compress,
    "pierce": pierce,
    "enter": enter,
    "beam": beam,
    "contain": contain,
    "fuse": fuse,
    "route": route,
    "zoom": zoom,
}
