# Domain 4: satellite downlink per pass (C3). Rate 2 MB/s = 7200 MB/h. Items count only if the last byte
# lands before the deadline. Programs plan the known queue over all known future passes, protect items
# that can only go now, order each pass by deadline (EDF) and fill the tail with a fragment.

RATE = 7200.0  # MB per hour
FRAG = 1000000000


def _cap(p):
    s, e, c = p
    return max(0.0, min(float(c), (e - s) * RATE))


def _dens(it):
    return it["value"] / max(1e-9, it["size"])


def _future(st):
    return [(i, st["passes"][i]) for i in range(st["t"], len(st["passes"]))]


def _fits_later(st, it):
    # can the item still go whole in some later pass before its deadline?
    for i, p in _future(st)[1:]:
        if p[0] >= it["deadline"]:
            break
        if _cap(p) >= it["size"] and p[0] + it["size"] / RATE < it["deadline"]:
            return True
    return False


def _edf_pack(st, chosen):
    # order chosen by deadline, keep those that make their deadline within current capacity
    p = st["passes"][st["t"]]
    cap = _cap(p)
    out, used = [], 0.0
    for it in sorted(chosen, key=lambda x: (x["deadline"], -_dens(x))):
        if used + it["size"] <= cap and p[0] + (used + it["size"]) / RATE < it["deadline"]:
            out.append(it)
            used += it["size"]
    return out, cap - used


def _fill(st, out, left, pool):
    p = st["passes"][st["t"]]
    have = set(x["id"] for x in out)
    used = _cap(p) - left
    for it in sorted(pool, key=lambda x: -_dens(x)):
        if it["id"] in have:
            continue
        if it["size"] <= left and p[0] + (used + it["size"]) / RATE < it["deadline"]:
            out.append(it)
            have.add(it["id"])
            left -= it["size"]
            used += it["size"]
    return out, left


def _frag(st, out, left):
    # fragment the densest remaining item whose remainder can still finish in later passes
    if left < 1:
        return None
    have = set(x["id"] for x in out)
    best = None
    for it in st["queue"]:
        if it["id"] in have or it["size"] <= left:
            continue
        rest = it["size"] - left
        room = 0.0
        for i, p in _future(st)[1:]:
            if p[0] >= it["deadline"]:
                break
            room += _cap(p)
            if room >= rest and p[0] + rest / RATE < it["deadline"]:
                break
        else:
            continue
        if room < rest:
            continue
        if best is None or _dens(it) > _dens(best):
            best = it
    return best


def _ids(out, frag):
    ids = [x["id"] for x in out]
    if frag is not None:
        ids.append(FRAG + frag["id"])
    return ids


def _late_plan(st):
    # densest-first, assign each item to the LATEST feasible pass with room (keeps early capacity free);
    # returns items that the plan puts in the current pass
    fut = _future(st)
    room = {i: _cap(p) for i, p in fut}
    load = {i: 0.0 for i, p in fut}
    now = []
    for it in sorted(st["queue"], key=lambda x: (-_dens(x), x["deadline"])):
        for i, p in reversed(fut):
            if p[0] >= it["deadline"]:
                continue
            if room[i] >= it["size"] and p[0] + (load[i] + it["size"]) / RATE < it["deadline"]:
                room[i] -= it["size"]
                load[i] += it["size"]
                if i == st["t"]:
                    now.append(it)
                break
    return now


# late_plan: plan the whole known queue over all future passes (densest first, latest feasible pass), send now
# what can only go now, fill the rest of the pass densest-first, EDF order, fragment the tail.
def late_plan(st):
    if not st["queue"]:
        return None
    out, left = _edf_pack(st, _late_plan(st))
    out, left = _fill(st, out, left, st["queue"])
    return _ids(out, _frag(st, out, left))


# must_now: items with no later feasible pass go first (densest first), then the rest by density;
# EDF order inside the pass; fragment the tail.
def must_now(st):
    if not st["queue"]:
        return None
    must = [it for it in st["queue"] if not _fits_later(st, it)]
    must.sort(key=lambda x: -_dens(x))
    p = st["passes"][st["t"]]
    cap, sel, used = _cap(p), [], 0.0
    for it in must:
        if used + it["size"] <= cap:
            sel.append(it)
            used += it["size"]
    out, left = _edf_pack(st, sel)
    out, left = _fill(st, out, left, st["queue"])
    return _ids(out, _frag(st, out, left))


# knap_now: exact value knapsack (10 MB grid) over the must-go-now items, so the pass holds the most value that
# would otherwise be lost; then densest fill, EDF order, tail fragment.
def knap_now(st):
    if not st["queue"]:
        return None
    p = st["passes"][st["t"]]
    cap = _cap(p)
    G = 10.0
    W = int(cap // G)
    must = [it for it in st["queue"] if not _fits_later(st, it) and p[0] + it["size"] / RATE < it["deadline"]]
    if must and W > 0 and len(must) * W <= 400000:
        best = [0.0] * (W + 1)
        keep = [[False] * (W + 1) for _ in must]
        for j, it in enumerate(must):
            w = int(-(-it["size"] // G))
            for c in range(W, w - 1, -1):
                v = best[c - w] + it["value"]
                if v > best[c]:
                    best[c] = v
                    keep[j][c] = True
        sel, c = [], W
        for j in range(len(must) - 1, -1, -1):
            if keep[j][c]:
                sel.append(must[j])
                c -= int(-(-must[j]["size"] // G))
    else:
        sel = []
    out, left = _edf_pack(st, sel)
    out, left = _fill(st, out, left, st["queue"])
    return _ids(out, _frag(st, out, left))


# edf_frag: the standard density order but sent in deadline order (so tight items in the same pass make it),
# plus a tail fragment instead of wasted capacity.
def edf_frag(st):
    if not st["queue"]:
        return None
    out, left = _fill(st, [], _cap(st["passes"][st["t"]]), st["queue"])
    out, left = _edf_pack(st, out)
    out, left = _fill(st, out, left, st["queue"])
    return _ids(out, _frag(st, out, left))


MOVES = {
    "late_plan": late_plan,
    "must_now": must_now,
    "knap_now": knap_now,
    "edf_frag": edf_frag,
}
