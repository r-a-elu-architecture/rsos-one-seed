# Domain 4: satellite downlink, one decision per pass. Pure functions of `st`.

_RATE_H = 2.0 * 3600.0  # MB per hour
_FRAG = 1000000000


def _pass(st, i):
    p = st["passes"][i]
    return float(p[0]), float(p[1]), float(p[2])


def _density(it):
    return float(it["value"]) / max(float(it["size"]), 1e-9)


def _fits_alone(st, i, it):
    s, e, cap = _pass(st, i)
    return it["size"] <= cap and s + it["size"] / _RATE_H < it["deadline"]


def _later_ok(st, it):
    # True if some later pass could still deliver the whole item before its deadline.
    for i in range(st["t"] + 1, len(st["passes"])):
        s, e, cap = _pass(st, i)
        if s >= it["deadline"]:
            break
        if _fits_alone(st, i, it):
            return True
    return False


def _pack(st, order):
    # Mirror of the runtime: pack in order, skip items that do not fit or would miss their deadline.
    s, e, cap = _pass(st, st["t"])
    used, out = 0.0, []
    for it in order:
        if used + it["size"] <= cap and s + (used + it["size"]) / _RATE_H < it["deadline"]:
            used += it["size"]
            out.append(it)
    return out, cap - used


def _edf(items):
    return sorted(items, key=lambda it: (it["deadline"], -_density(it)))


def _finalize(st, chosen, frag=True):
    # Order the chosen set by deadline (so every chosen item meets its deadline), fill with density order,
    # then put a fragment of the best item that still has a later pass into the unused tail.
    q = st["queue"]
    ids = set(it["id"] for it in chosen)
    rest = sorted([it for it in q if it["id"] not in ids], key=lambda it: -_density(it))
    packed, left = _pack(st, _edf(chosen) + rest)
    out = [it["id"] for it in _edf(packed)]
    # re-check EDF order of the packed set is still feasible; else keep packing order
    if len(_pack(st, _edf(packed))[0]) != len(packed):
        out = [it["id"] for it in packed]
    if frag and left > 0:
        pid = set(out)
        s, e, cap = _pass(st, st["t"])
        cands = [it for it in q if it["id"] not in pid and it["size"] > left and _later_ok(st, it)]
        if cands:
            best = max(cands, key=lambda it: (_density(it), -it["deadline"]))
            out.append(_FRAG + best["id"])
    return out


def _knap(items, cap):
    # 0/1 knapsack on value with sizes rounded up to whole MB (exact enough for 20-600 MB items).
    capi = int(cap)
    if capi <= 0 or not items:
        return []
    w = [max(1, int(-(-it["size"] // 1))) for it in items]
    best = [0.0] * (capi + 1)
    keep = [[False] * (capi + 1) for _ in items]
    for j, it in enumerate(items):
        wj, vj = w[j], float(it["value"])
        for c in range(capi, wj - 1, -1):
            if best[c - wj] + vj > best[c]:
                best[c] = best[c - wj] + vj
                keep[j][c] = True
    out, c = [], capi
    for j in range(len(items) - 1, -1, -1):
        if keep[j][c]:
            out.append(items[j])
            c -= w[j]
    return out


def _deliverable_now(st):
    s, e, cap = _pass(st, st["t"])
    return [it for it in st["queue"] if _fits_alone(st, st["t"], it)]


# expiring_knapsack: items with no later pass before their deadline are now-or-never; pick the value-maximal
# subset of them by knapsack (density greedy wastes capacity on large items), then fill by density, then a
# fragment of the best still-deliverable item in the tail.
def expiring_knapsack(st):
    if not st.get("queue"):
        return None
    now = _deliverable_now(st)
    exp = [it for it in now if not _later_ok(st, it)]
    s, e, cap = _pass(st, st["t"])
    chosen = _knap(exp, cap)
    chosen = _pack(st, _edf(chosen))[0]
    return _finalize(st, chosen)


# lookahead_assign: multi-pass plan over known passes. Items in density order are assigned to the LATEST pass
# that can still deliver them, keeping early capacity for tight-deadline items; this pass sends what the plan
# assigns to it (deadline order), then fills by density and adds a tail fragment.
def lookahead_assign(st):
    q = st.get("queue")
    if not q:
        return None
    t = st["t"]
    n = len(st["passes"])
    rem = {i: _pass(st, i)[2] for i in range(t, n)}
    here = []
    for it in sorted(q, key=lambda it: -_density(it)):
        for i in range(n - 1, t - 1, -1):
            s, e, cap = _pass(st, i)
            if s >= it["deadline"]:
                continue
            if it["size"] <= rem[i] and s + (cap - rem[i] + it["size"]) / _RATE_H < it["deadline"]:
                rem[i] -= it["size"]
                if i == t:
                    here.append(it)
                break
    return _finalize(st, here)


# density_edf_frag: the standard's value-per-MB choice, but sent in deadline order so no chosen item misses its
# deadline inside the pass, plus a fragment of the best remaining item in the unused tail.
def density_edf_frag(st):
    q = st.get("queue")
    if not q:
        return None
    chosen = _pack(st, sorted(q, key=lambda it: -_density(it)))[0]
    return _finalize(st, chosen)


# urgency_value: score = value per MB, boosted x3 for items whose last chance is this pass and x1.5 for items
# whose only later chance is the next pass; capacity goes to value that would otherwise be lost.
def urgency_value(st):
    q = st.get("queue")
    if not q:
        return None
    t = st["t"]

    def chances(it):
        c = 0
        for i in range(t + 1, len(st["passes"])):
            s, e, cap = _pass(st, i)
            if s >= it["deadline"]:
                break
            if _fits_alone(st, i, it):
                c += 1
        return c

    def score(it):
        c = chances(it)
        boost = 3.0 if c == 0 else (1.5 if c == 1 else 1.0)
        return _density(it) * boost

    chosen = _pack(st, sorted(q, key=lambda it: -score(it)))[0]
    return _finalize(st, chosen)


MOVES = {
    "expiring_knapsack": expiring_knapsack,
    "lookahead_assign": lookahead_assign,
    "density_edf_frag": density_edf_frag,
    "urgency_value": urgency_value,
}
