# RSOS decision programs, domain 4: an Earth-observation satellite downlinking over ground-station passes (CONF4, R1).
# Host = computer (on-board scheduler): V (see the queue and every known pass) -> A (the room by the pass's state:
# stable = everything fits; overload = more than the pass can carry) -> K (compose the pass list in order) -> O (trace:
# which item can still land in a later pass, which cannot) -> G (value delivered before deadlines).
# Pure functions of st; Python standard library only.

RATE = 7200.0          # MB per hour (2 MB/s)
FRAG = 1000000000


def _pass(st, k):
    p = st["passes"][k]
    return float(p[0]), float(p[1]), float(p[2])


def _dens(it):
    return float(it["value"]) / max(float(it["size"]), 1e-9)


def _later_ok(st, size, deadline, used=None, reserve=1.0):
    # O: can this size still land in some LATER pass before its deadline? (ignores the current pass)
    P = st["passes"]
    for k in range(st["t"] + 1, len(P)):
        s, e, c = _pass(st, k)
        if s >= deadline:
            break
        u = used.get(k, 0.0) if used else 0.0
        if u + size <= c * reserve and s + (u + size) / RATE <= deadline:
            return True
    return False


def _edf_ok(start, cap, items):
    # K check: the set fits the capacity and every item finishes before its deadline in deadline order
    # (deadline order is the order that makes a set feasible if any order does).
    tot = 0.0
    for it in sorted(items, key=lambda x: (x["deadline"], -_dens(x))):
        tot += float(it["size"])
        if tot > cap + 1e-9 or start + tot / RATE > float(it["deadline"]) + 1e-12:
            return False
    return True


def _select(st, ordered):
    # greedy in the given priority order, each item kept only if the whole set stays EDF-feasible
    s, e, cap = _pass(st, st["t"])
    chosen = []
    for it in ordered:
        if s + float(it["size"]) / RATE > float(it["deadline"]):
            continue
        if _edf_ok(s, cap, chosen + [it]):
            chosen.append(it)
    return sorted(chosen, key=lambda x: (x["deadline"], -_dens(x)))


def _fragment(st, chosen):
    # Green particle landing at the place of need (U102, U161, U167) bounded by the deficit (U103):
    # simulate the standard's fill after our list, read the tail no whole item fits, and land a fragment of the item
    # whose remainder is worth most per remaining MB and can still be completed in a later pass before its deadline.
    s, e, cap = _pass(st, st["t"])
    used = sum(float(it["size"]) for it in chosen)
    ids = set(it["id"] for it in chosen)
    rest = [it for it in st["queue"] if it["id"] not in ids]
    for it in sorted(rest, key=lambda x: -_dens(x)):
        sz = float(it["size"])
        if used + sz <= cap and s + (used + sz) / RATE <= float(it["deadline"]):
            used += sz
            ids.add(it["id"])
    tail = cap - used
    if tail < 1.0:
        return None
    best, best_v = None, 0.0
    for it in st["queue"]:
        if it["id"] in ids:
            continue
        r = float(it["size"]) - tail
        if r <= 0:
            continue
        if not _later_ok(st, r, float(it["deadline"])):
            continue
        v = float(it["value"]) / r
        if v > best_v:
            best, best_v = it, v
    return None if best is None else FRAG + int(best["id"])


def _out(st, chosen, frag=True):
    out = [int(it["id"]) for it in chosen]
    if frag:
        f = _fragment(st, chosen)
        if f is not None:
            out.append(f)
    return out if out else None


def _all_fit(st):
    s, e, cap = _pass(st, st["t"])
    live = [it for it in st["queue"] if s + float(it["size"]) / RATE <= float(it["deadline"])]
    return live, _edf_ok(s, cap, live)


def _need_first(st):
    # Law 4 landing: an item that cannot land in any later pass is needed NOW; an item that can is withheld
    # (withholding is a move), unless capacity is left. Within each group: value per MB (Lion: the boldest value).
    q = st["queue"]
    return sorted(q, key=lambda it: (0 if not _later_ok(st, float(it["size"]), float(it["deadline"])) else 1,
                                     -_dens(it), it["deadline"]))


def _alap(st, reserve):
    # P5 value carried back across all known passes (job sequencing with deadlines): items by value per MB,
    # each placed in the LATEST pass where it still lands before its deadline (future passes counted at `reserve` of
    # their capacity, leaving room for items that arrive later); the items that land only now form this pass.
    P = st["passes"]
    t = st["t"]
    used = {}
    now = []
    for it in sorted(st["queue"], key=lambda x: (-_dens(x), x["deadline"])):
        sz, dl = float(it["size"]), float(it["deadline"])
        placed = False
        last = None
        for k in range(t + 1, len(P)):
            s, e, c = _pass(st, k)
            if s >= dl:
                break
            u = used.get(k, 0.0)
            if u + sz <= c * reserve and s + (u + sz) / RATE <= dl:
                last = k
        if last is not None:
            used[last] = used.get(last, 0.0) + sz
            placed = True
        if not placed:
            now.append(it)
    # this pass: the items with no later place first (by value per MB), then everything else by value per MB
    rest = [it for it in sorted(st["queue"], key=lambda x: -_dens(x)) if it not in now]
    return _select(st, now + rest)


# need_edf_fragment
# Rooms: STABLE (every live item fits this pass in deadline order) -> send all, deadline order, fragment in the tail |
#   OVERLOAD (more than the pass carries) -> items with no later pass first (Law 4: the need is in the item's own
#   future), then by value per MB; deadline order inside the pass; fragment landing in the tail.
# Chain (V->A->K->O->G): see queue + passes -> room by fit -> need-first selection -> deadline order (Tiger: the
#   precise path, no item late inside the pass) -> trace of later passes -> fragment -> delivered value.
# Laws: Law 4 (land where it changes the item's future; withhold what can land later), Law 6 (capacity, graceful
#   loss: the lowest-value items drop first), Law 1' (only size, value, deadline, passes read), Law 0 (no listed item
#   is sent late: each set is checked EDF-feasible), U102/U103 (fragment at the place of need, bounded by the tail).
# Invariant: every listed whole item finishes before its deadline; the pass is filled to capacity.
# Check: delivered value >= the standard's.
def need_edf_fragment(st):
    if not st.get("queue"):
        return None
    live, fit = _all_fit(st)
    if fit:
        return _out(st, sorted(live, key=lambda x: (x["deadline"], -_dens(x))))
    return _out(st, _select(st, _need_first(st)))


# alap_reserve_85
# Rooms: STABLE -> send all live items, deadline order, fragment | OVERLOAD -> value carried back over every known pass
#   (P5): each item by value per MB booked into the latest pass where it still lands (future passes at 85 % capacity,
#   15 % kept for items that arrive later); this pass = the items with no later place, then the standard fill.
# Chain: see -> room -> plan the whole horizon (observer from above, U150; past/present/future) -> this pass's part ->
#   deadline order -> fragment.
# Laws: Law 4, P5, Law 6, Law 0 (feasibility check), Law 5 (the known passes are relations that raise the limit).
# Invariant: every listed item lands before its deadline; reserve keeps future room.
# Check: delivered value >= the standard's.
def alap_reserve_85(st):
    if not st.get("queue"):
        return None
    live, fit = _all_fit(st)
    if fit:
        return _out(st, sorted(live, key=lambda x: (x["deadline"], -_dens(x))))
    return _out(st, _alap(st, 0.85))


# alap_reserve_60
# Rooms and chain as alap_reserve_85, with future passes booked at 60 % (more room kept for later alerts: the
#   host's future arrivals are part of its own future, Law 4).
# Laws: Law 4, P5, Law 6, Law 0.
# Invariant / check: as alap_reserve_85.
def alap_reserve_60(st):
    if not st.get("queue"):
        return None
    live, fit = _all_fit(st)
    if fit:
        return _out(st, sorted(live, key=lambda x: (x["deadline"], -_dens(x))))
    return _out(st, _alap(st, 0.60))


# dragon_repair_standard
# Rooms: ANY -> the standard's own set (value per MB, greedy) repaired only where it differs from a feasible pass
#   (White Dragon U90 / P3: keep the whole, heal the part): items the standard order would deliver late are re-ordered
#   by deadline; the wasted tail gets a fragment.
# Chain: see -> the standard's set -> heal the order (deadline) -> fragment -> delivered value.
# Laws: Law 3 (living structure: repair only the part that differs), Law 0, U102/U103 (fragment), Law 1'.
# Invariant: the set is the standard's greedy set or a superset reached by the feasible reorder.
# Check: delivered value >= the standard's in every pass.
def dragon_repair_standard(st):
    if not st.get("queue"):
        return None
    return _out(st, _select(st, sorted(st["queue"], key=lambda x: (-_dens(x), x["deadline"]))))


# house_route
# Rooms: STABLE (all live items fit) -> all, deadline order, fragment | URGENT (some item with value per MB above the
#   queue's median has no later pass) -> need_edf (Law 4 first) | CROWDED (otherwise) -> P5 horizon plan at 85 %.
# Chain: see -> room by state (U5, U69) -> the room's selection -> deadline order -> fragment.
# Laws: Law 4, P5, Law 3, Law 6, Law 0, route by state.
# Invariant: every listed item lands before its deadline.
# Check: delivered value >= the standard's and >= each single room's program on the same passes.
def house_route(st):
    q = st.get("queue")
    if not q:
        return None
    live, fit = _all_fit(st)
    if fit:
        return _out(st, sorted(live, key=lambda x: (x["deadline"], -_dens(x))))
    ds = sorted(_dens(it) for it in q)
    med = ds[len(ds) // 2]
    urgent = [it for it in live if _dens(it) >= med and not _later_ok(st, float(it["size"]), float(it["deadline"]))]
    if urgent:
        return _out(st, _select(st, _need_first(st)))
    return _out(st, _alap(st, 0.85))


MOVES = {
    "need_edf_fragment": need_edf_fragment,
    "alap_reserve_85": alap_reserve_85,
    "alap_reserve_60": alap_reserve_60,
    "dragon_repair_standard": dragon_repair_standard,
    "house_route": house_route,
}
