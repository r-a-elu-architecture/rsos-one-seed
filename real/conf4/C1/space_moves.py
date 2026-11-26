# Domain 4: Earth-observation downlink, one ordered id list per pass. Programs plan across known future passes.

RATE_MB_PER_H = 2.0 * 3600.0
FRAG = 1000000000
EPS = 1e-9


def _dens(it):
    return it["value"] / max(it["size"], 1e-6)


def _fits(items, pas):
    """Items fit pass (start, end, cap) when sent in deadline order, all finishing before their deadlines."""
    s, e, cap = pas[0], pas[1], pas[2]
    if sum(i["size"] for i in items) > cap + EPS:
        return False
    cum = 0.0
    for it in sorted(items, key=lambda i: i["deadline"]):
        cum += it["size"]
        fin = s + cum / RATE_MB_PER_H
        if fin >= it["deadline"] - EPS or fin > e + EPS:
            return False
    return True


def _horizon(st):
    t, P = st["t"], st["passes"]
    q = st.get("queue") or []
    if not q:
        return []
    last = max(i["deadline"] for i in q)
    return [tuple(p) for p in P[t:] if p[0] < last][:60] or [tuple(P[t])]


def _edf(items):
    return [i["id"] for i in sorted(items, key=lambda i: (i["deadline"], -_dens(i)))]


def _fill_forward(now, pool, pas):
    for it in sorted(pool, key=lambda i: -_dens(i)):
        if it not in now and _fits(now + [it], pas):
            now.append(it)
    return now


def _fragment(st, now, H, future_assign=None):
    """Tail fragment: an item not sent whole now whose remainder can finish in a later pass before deadline."""
    pas = H[0]
    rem = pas[2] - sum(i["size"] for i in now)
    if rem <= 1.0 or len(H) < 2:
        return None
    used = sum(i["size"] for i in now)
    tail_end = pas[0] + (used + rem) / RATE_MB_PER_H
    best, bkey = None, None
    for it in st.get("queue") or []:
        if it in now or it["size"] <= rem:
            continue
        if tail_end >= it["deadline"]:
            continue
        left = it["size"] - rem
        ok = False
        for p in H[1:]:
            if p[0] + left / RATE_MB_PER_H < it["deadline"] - EPS and left <= p[2]:
                ok = True
                break
        if not ok:
            continue
        planned = 1 if (future_assign and it["id"] in future_assign) else 0
        key = (planned, _dens(it), -it["deadline"])
        if bkey is None or key > bkey:
            best, bkey = it, key
    return None if best is None else FRAG + best["id"]


def _lazy_plan(st):
    """Density-ordered assignment of every queued item to the LATEST pass that can still deliver it, so the
    current pass is reserved for items that have no later chance; returns (now_items, future_ids)."""
    q = list(st.get("queue") or [])
    H = _horizon(st)
    if not H:
        return [], set(), H
    assign = [[] for _ in H]
    placed = {}
    for it in sorted(q, key=lambda i: -_dens(i)):
        for pi in range(len(H) - 1, -1, -1):
            if _fits(assign[pi] + [it], H[pi]):
                assign[pi].append(it)
                placed[it["id"]] = pi
                break
    now = list(assign[0])
    future = {i for i, p in placed.items() if p > 0}
    # pull forward: anything that fits now goes now (frees later capacity for future arrivals, esp. alerts)
    now = _fill_forward(now, [i for i in q if i not in now], H[0])
    future -= {i["id"] for i in now}
    return now, future, H


# lazy_plan_frag: latest-feasible-pass planning (items with no later chance get this pass first), pull
# everything else forward by value density, send in deadline order, fill the tail with a fragment of an item
# whose remainder still meets its deadline later.
def lazy_plan_frag(st):
    now, future, H = _lazy_plan(st)
    if not H:
        return None
    out = _edf(now)
    f = _fragment(st, now, H, future)
    if f is not None:
        out.append(f)
    return out or None


# lazy_plan: the same plan without a fragment (hedge in case partial transfers displace later whole items).
def lazy_plan(st):
    now, future, H = _lazy_plan(st)
    return _edf(now) or None


# urgent_knapsack: exact 0/1 knapsack on this pass where items that cannot make any later pass are weighted
# 20x (their value is lost otherwise); then deadline-feasibility repair, density fill, EDF order, fragment.
def urgent_knapsack(st):
    q = list(st.get("queue") or [])
    H = _horizon(st)
    if not H or not q:
        return None
    pas = H[0]
    cap = int(pas[2])

    def later_ok(it):
        for p in H[1:]:
            if p[0] + it["size"] / RATE_MB_PER_H < it["deadline"] - EPS and it["size"] <= p[2]:
                return True
        return False

    cand = [i for i in q if _fits([i], pas)]
    if not cand:
        return None
    W = [max(1, int(round(i["size"]))) for i in cand]
    V = [i["value"] * (1.0 if later_ok(i) else 20.0) for i in cand]
    scale = 1
    while cap // scale * len(cand) > 400000:
        scale *= 2
    C = cap // scale
    Ws = [-(-w // scale) for w in W]
    dp = [0.0] * (C + 1)
    keep = [[False] * (C + 1) for _ in cand]
    for n, (w, v) in enumerate(zip(Ws, V)):
        for c in range(C, w - 1, -1):
            if dp[c - w] + v > dp[c]:
                dp[c] = dp[c - w] + v
                keep[n][c] = True
    c, chosen = C, []
    for n in range(len(cand) - 1, -1, -1):
        if keep[n][c]:
            chosen.append(cand[n])
            c -= Ws[n]
    # repair deadlines: drop lowest weighted value until feasible
    wv = {i["id"]: v for i, v in zip(cand, V)}
    chosen.sort(key=lambda i: -wv[i["id"]])
    while chosen and not _fits(chosen, pas):
        chosen.pop()
    chosen = _fill_forward(chosen, [i for i in q if i not in chosen], pas)
    out = _edf(chosen)
    f = _fragment(st, chosen, H)
    if f is not None:
        out.append(f)
    return out or None


# density_edf_frag: the standard's value-per-MB selection, but sent in deadline order (so more items meet their
# deadlines inside the pass) plus a tail fragment instead of wasted capacity.
def density_edf_frag(st):
    q = list(st.get("queue") or [])
    H = _horizon(st)
    if not H or not q:
        return None
    now = _fill_forward([], q, H[0])
    out = _edf(now)
    f = _fragment(st, now, H)
    if f is not None:
        out.append(f)
    return out or None


# alert_first: alerts (highest value density, shortest deadlines) in deadline order, then the lazy plan's
# remaining items; guards against alerts being skipped when big science items precede them.
def alert_first(st):
    q = list(st.get("queue") or [])
    H = _horizon(st)
    if not H or not q:
        return None
    pas = H[0]
    now = []
    for it in sorted([i for i in q if i.get("cls") == "alert"], key=lambda i: i["deadline"]):
        if _fits(now + [it], pas):
            now.append(it)
    lp, future, _ = _lazy_plan(st)
    for it in lp:
        if it not in now and _fits(now + [it], pas):
            now.append(it)
    now = _fill_forward(now, [i for i in q if i not in now], pas)
    out = _edf(now)
    f = _fragment(st, now, H, future)
    if f is not None:
        out.append(f)
    return out or None


MOVES = {
    "lazy_plan_frag": lazy_plan_frag,
    "lazy_plan": lazy_plan,
    "urgent_knapsack": urgent_knapsack,
    "density_edf_frag": density_edf_frag,
    "alert_first": alert_first,
}
