"""Composed RSOS moves for two AI agents answering a 4-hop question (domain 3).

The question's chain: X -manager-> M -team-> T -office-> O -city-> C.
Grammar: composition; the sequence of operators is the program, in VAKOG order
(see -> choose -> act -> trace -> result). Each move returns ONE native action: a list of at
most 2 fact keys from st["unsent"], or None.
"""

CHAIN = ("manager", "team", "office", "city")
HOP = {r: i for i, r in enumerate(CHAIN)}


# ---------------------------------------------------------------- operators
def see(st):
    """V: what A can see: its own facts, B's facts received, what is still unsent."""
    known = dict(st.get("mine") or {})
    known.update(dict(st.get("received") or {}))
    raw = list(st.get("unsent") or [])
    unsent = [tuple(k) for k in raw]
    return {"orig": dict(zip(unsent, raw)), "x": st.get("x"), "known": known, "mine": dict(st.get("mine") or {}),
            "received": dict(st.get("received") or {}), "unsent": unsent, "uset": set(unsent)}


def trace(v):
    """O: walk the chain from X through every fact either agent has put on the table;
    the path so far and where it breaks (the frontier)."""
    path, subj = [], v["x"]
    for rel in CHAIN:
        k = (rel, subj)
        if k not in v["known"]:
            break
        path.append(k)
        subj = v["known"][k]
    v["path"], v["frontier"] = path, (CHAIN[len(path)] if len(path) < len(CHAIN) else None, subj)
    ents = {v["x"]}
    for k in path:
        ents.add(v["known"][k])
    for (r, s), val in v["received"].items():
        ents.add(s)
        ents.add(val)
    v["ents"] = ents
    return v


def contain(keys, v):
    """Membrane: only chain-relation facts that are still unsent (mentor / home are dropped)."""
    return [k for k in keys if k in v["uset"] and k[0] in HOP]


def fragments(v):
    """Compress A's own chain facts into linked fragments (value of one = subject of the next hop)."""
    mine = {k: val for k, val in v["mine"].items() if k[0] in HOP}
    links = []
    for (r1, s1), val in mine.items():
        i = HOP[r1]
        if i + 1 < len(CHAIN):
            k2 = (CHAIN[i + 1], val)
            if k2 in mine:
                links.append(((r1, s1), k2))
    return links


def choose(keys, n=2):
    """A: the first n distinct keys."""
    out = []
    for k in keys:
        if k not in out:
            out.append(k)
        if len(out) >= n:
            break
    return out


def act(keys, v):
    """K: land a message, only if something lands (keys given back exactly as in st["unsent"])."""
    return [v["orig"].get(k, k) for k in keys] if keys else None


# ---------------------------------------------------------------- moves
# see > trace > pierce > contain > act: walk the chain through everything on the table and send
# exactly A's unsent facts on that path, hop order (the facts the answer is made of).
def m_path(st):
    v = trace(see(st))
    return act(choose(contain(v["path"], v)), v)


# see > trace > fuse > contain > act: across agents: A's chain facts whose subject is an entity
# already on the table (X, path values, anything B has sent), nearest hop first; this joins
# A's half to B's half where they touch.
def m_fuse(st):
    v = trace(see(st))
    nxt = v["frontier"]
    cands = [k for k in v["unsent"] if k[0] in HOP and k[1] in v["ents"]]
    cands.sort(key=lambda k: (0 if nxt and k == nxt else 1, HOP[k[0]]))
    return act(choose(contain(cands, v)), v)


# see > trace > compress > inherit > contain > act: A's own facts compressed into linked fragments
# (office->city, team->office, ...); the fragment nearest the answer goes first, so B, holding
# the upper hops, inherits a whole working tail and can finish the chain.
def m_fragment(st):
    v = trace(see(st))
    links = fragments(v)
    links.sort(key=lambda kk: (-HOP[kk[1][0]], 0 if kk[0][1] in v["ents"] else 1))
    keys = []
    for a, b in links:
        if a in v["uset"] and b in v["uset"]:
            keys += [a, b]
    return act(choose(contain(keys, v)), v)


# see > trace > choose > contain > act: the standard relevance order with the membrane on it:
# subject X first, then subjects on the table, then the rest; only chain relations, so no
# distractor (mentor, home) uses the channel.
def m_relevant(st):
    v = trace(see(st))
    def rank(k):
        tier = 0 if k[1] == v["x"] else (1 if k[1] in v["ents"] else 2)
        return (tier, HOP.get(k[0], 9))
    cands = sorted(contain(v["unsent"], v), key=rank)
    return act(choose(cands), v)


MOVES = {
    "see>trace>pierce>contain>act": m_path,
    "see>trace>fuse>contain>act": m_fuse,
    "see>trace>compress>inherit>contain>act": m_fragment,
    "see>trace>choose>contain>act": m_relevant,
}
