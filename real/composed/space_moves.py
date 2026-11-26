"""Composed RSOS moves for an Earth-observation satellite downlink (domain 4).

Grammar: composition; the sequence of operators is the program, in VAKOG order
(see -> choose -> act -> trace -> result), across time (past arrivals, the present pass,
the future passes known in advance). Each move returns ONE native action: an ordered list
of item ids for this pass, or None.
"""

RATE_MB_PER_H = 2.0 * 3600.0  # 2 MB/s


# ---------------------------------------------------------------- operators
def see(st):
    """V: the present pass and the queue on board."""
    passes = [tuple(p) for p in (st.get("passes") or [])]
    t = int(st.get("t", 0) or 0)
    cur = passes[t] if 0 <= t < len(passes) else (0.0, 0.0, 0.0)
    q = [dict(i) for i in (st.get("queue") or [])]
    return {"t": t, "passes": passes, "cur": cur, "queue": q}


def density(i):
    return float(i.get("value", 0)) / max(float(i.get("size", 1)), 1e-9)


def future(v):
    """Across time: can each item still land in a later pass (sent first there, before its
    deadline)? Items that cannot are now-or-never."""
    later = v["passes"][v["t"] + 1:]
    for i in v["queue"]:
        sz, dl = float(i["size"]), float(i["deadline"])
        i["_later"] = any(cap >= sz and s + sz / RATE_MB_PER_H < dl and s + sz / RATE_MB_PER_H <= e
                          for s, e, cap in later)
    return v


def simulate(order, v):
    """K applied in order: pack into this pass, skipping items that would miss capacity,
    the pass end or their deadline; returns the items that land."""
    s, e, cap = v["cur"]
    used, out = 0.0, []
    for i in order:
        sz = float(i["size"])
        if used + sz > cap:
            continue
        fin = s + (used + sz) / RATE_MB_PER_H
        if fin >= float(i["deadline"]) or fin > e:
            continue
        used += sz
        out.append(i)
    return out


def edf(items):
    """Contain the deadlines: earliest deadline first inside the pass (for a common start this
    order lands every set that any order can land)."""
    return sorted(items, key=lambda i: (float(i["deadline"]), -density(i)))


def select_then_order(order, v):
    """Choose the set greedily in `order`, then send it EDF; the rest follows in `order`.
    Each candidate joins only if the whole EDF-ordered set still lands."""
    chosen = []
    for i in order:
        trial = edf(chosen + [i])
        if len(simulate(trial, v)) == len(trial):
            chosen = trial
    rest = [i for i in order if i not in chosen]
    return chosen + rest


def act(items):
    """Land the ordered ids, only if there is something to send."""
    ids = [i["id"] for i in items]
    return ids if ids else None


CLASS_RANK = {"alert": 0, "science": 1, "bulk": 2}


def knapsack(items, cap, weight):
    """Choose the set of most total weighted value within capacity (DP over 5 MB units)."""
    unit = 5.0
    C = int(cap // unit)
    if C <= 0 or not items:
        return []
    ws = [max(1, int(-(-float(i["size"]) // unit))) for i in items]
    best = [0.0] * (C + 1)
    keep = [[False] * (C + 1) for _ in items]
    for n, i in enumerate(items):
        w, val = ws[n], weight(i)
        for c in range(C, w - 1, -1):
            if best[c - w] + val > best[c]:
                best[c] = best[c - w] + val
                keep[n][c] = True
    out, c = [], C
    for n in range(len(items) - 1, -1, -1):
        if keep[n][c]:
            out.append(items[n])
            c -= ws[n]
    return out


# ---------------------------------------------------------------- moves
# see > choose > contain > act: the standard's value-per-MB choice, but sent earliest-deadline
# first, so no chosen item is skipped only because of its place in the order.
def m_density_edf(st):
    v = see(st)
    order = sorted(v["queue"], key=lambda i: -density(i))
    return act(select_then_order(order, v))


# see > future > triage > contain > act: across time: now-or-never items (no later pass can
# land them) are chosen first by value per MB, deferrable items after; sent EDF.
def m_triage(st):
    v = future(see(st))
    order = sorted(v["queue"], key=lambda i: (i["_later"], -density(i)))
    return act(select_then_order(order, v))


# see > colour > route > contain > act: from above: colour by class (alert > science > bulk),
# route each class by deadline, choose in that order, send EDF.
def m_colour(st):
    v = see(st)
    order = sorted(v["queue"], key=lambda i: (CLASS_RANK.get(i.get("cls"), 3),
                                              float(i["deadline"]), -density(i)))
    return act(select_then_order(order, v))


# see > future > compress > inherit > contain > act: compress the pass into one whole choice
# (knapsack on value, deferrable items weighted down because a later pass can still carry
# them); the chosen set goes first, EDF, then the rest by value per MB.
def m_knapsack(st):
    v = future(see(st))
    s, e, cap = v["cur"]
    cap = min(float(cap), max(0.0, (e - s) * RATE_MB_PER_H)) if e > s else float(cap)
    feas = [i for i in v["queue"] if simulate([i], v)]
    pick = knapsack(feas, cap, lambda i: float(i["value"]) * (0.35 if i["_later"] else 1.0))
    rest = sorted([i for i in v["queue"] if i not in pick], key=lambda i: -density(i))
    order = sorted(pick, key=lambda i: -float(i["value"])) + rest
    return act(select_then_order(order, v))


MOVES = {
    "see>choose>contain>act": m_density_edf,
    "see>future>triage>contain>act": m_triage,
    "see>colour>route>contain>act": m_colour,
    "see>future>compress>inherit>contain>act": m_knapsack,
}
