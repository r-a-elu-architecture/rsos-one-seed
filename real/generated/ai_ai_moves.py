"""RSOS operator moves for the AI-AI fact-exchange host (A's message per round).

Each move: st -> list of at most 2 fact keys from st["unsent"], or None when the operator does not apply.
Chain of the question: X -manager-> M -team-> T -office-> O -city-> C.
"""

CHAIN = ("manager", "team", "office", "city")


def _known(st):
    k = dict(st["mine"])
    k.update(st["received"])
    return k


def _walk(st):
    """Follow the chain through what A knows. Returns (hop keys resolved, frontier index, frontier subject)."""
    known, subj, keys = _known(st), st["x"], []
    for i, r in enumerate(CHAIN):
        key = (r, subj)
        if key not in known:
            return keys, i, subj
        keys.append(key)
        subj = known[key]
    return keys, len(CHAIN), subj


def _pick(st, keys):
    unsent, out = set(st["unsent"]), []
    for k in keys:
        if k in unsent and k not in out:
            out.append(k)
        if len(out) == 2:
            break
    return out or None


def _nxt(r):
    return CHAIN[CHAIN.index(r) + 1] if r in CHAIN and r != CHAIN[-1] else None


# PIERCE: pierce through the hops A can resolve and send A's own unsent links of the answer chain, in hop order.
def pierce(st):
    keys, _, _ = _walk(st)
    return _pick(st, [k for k in keys if k in st["mine"]])


# BEAM: chain stuck at a hop B holds -> whole message on A's facts of the following relation (the missing hop's target).
def beam(st):
    _, i, _ = _walk(st)
    if i >= len(CHAIN) - 1:
        return None
    r = CHAIN[i + 1]
    return _pick(st, [k for k in st["unsent"] if k[0] == r])


# HEAL: repair the link B's messages left open: for each received chain fact (latest first), send A's next-hop fact on its value.
def heal(st):
    cands = []
    for (r, s), v in reversed(list(st["received"].items())):
        n = _nxt(r)
        if n and (n, v) in st["mine"]:
            cands.append((n, v))
    return _pick(st, cands)


# CONTAIN: the standard ranking with distractor relations (mentor, home) and off-chain subjects contained out.
def contain(st):
    known, x = _known(st), st["x"]
    linked = {(_nxt(r), v) for (r, s), v in known.items() if _nxt(r)}
    def tier(k):
        if k[1] == x and k[0] == "manager":
            return 0
        if k in linked:
            return 1
        return 2
    cands = [k for k in st["unsent"] if k[0] in CHAIN]
    return _pick(st, sorted(cands, key=tier))


# COMPRESS: two hops in one message: a linked pair of A's facts (r_i, s)->v and (r_i+1, v), from the frontier onward.
def compress(st):
    _, i0, _ = _walk(st)
    mine, unsent = st["mine"], set(st["unsent"])
    pairs = []
    for (r, s), v in mine.items():
        n = _nxt(r)
        if n and (r, s) in unsent and (n, v) in unsent and CHAIN.index(r) >= min(i0, len(CHAIN) - 2):
            pairs.append((CHAIN.index(r), (r, s), (n, v)))
    if not pairs:
        return None
    pairs.sort(key=lambda p: p[0])
    return [pairs[0][1], pairs[0][2]]


# INHERIT: carry the O-trace on: every entity already in the conversation inherits its next chain hop from A's facts (deepest first).
def inherit(st):
    trace = [(k, v) for k, v in st["received"].items()]
    trace += [(k, st["mine"][k]) for k in st["sent_A"] if k in st["mine"]]
    cands = []
    for (r, s), v in trace:
        n = _nxt(r)
        if n and (n, v) in st["mine"]:
            cands.append((CHAIN.index(n), (n, v)))
    cands.sort(key=lambda c: -c[0])
    return _pick(st, [k for _, k in cands])


# FUSE: joint message: one slot advances the known chain (pierce/heal), the other is beamed at the hop beyond the frontier.
def fuse(st):
    a = (pierce(st) or heal(st) or [])[:1]
    b = [k for k in (beam(st) or []) if k not in a][:1]
    out = a + b
    return out if len(out) == 2 else None


# ROUTE BY STATE (colour): green = A holds chain links -> pierce; amber = B opened a link -> heal; red = stuck -> beam.
def route(st):
    return pierce(st) or heal(st) or beam(st)


# ZOOM: change scale to the answer end of the chain: city facts on any known office, else office facts on any known team.
def zoom(st):
    known = _known(st)
    offices = {v for (r, s), v in known.items() if r == "office"}
    teams = {v for (r, s), v in known.items() if r == "team"}
    c = [k for k in st["unsent"] if k[0] == "city" and k[1] in offices]
    c += [k for k in st["unsent"] if k[0] == "office" and k[1] in teams]
    return _pick(st, c)


MOVES = {
    "pierce": pierce,
    "beam": beam,
    "heal": heal,
    "contain": contain,
    "compress": compress,
    "inherit": inherit,
    "fuse": fuse,
    "route": route,
    "zoom": zoom,
}
