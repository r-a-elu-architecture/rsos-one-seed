# Domain 3: A's message in a two-agent 4-hop question. Pure functions of `st`.
# Chain: X -manager-> M -team-> T -office-> O -city-> answer.

_CHAIN = ["manager", "team", "office", "city"]


def _known(st):
    k = dict(st.get("received") or {})
    k.update(st.get("mine") or {})
    return k


def _walk(st):
    # Follow the chain over everything A knows. Returns (path keys, gap key or None).
    known = _known(st)
    cur = st.get("x")
    path = []
    for rel in _CHAIN:
        key = (rel, cur)
        if key in known:
            path.append(key)
            cur = known[key]
        else:
            return path, key
    return path, None


def _unsent(st):
    return [tuple(k) if isinstance(k, list) else k for k in (st.get("unsent") or [])]


def _chain_facts(st):
    # A's own unsent facts on the resolved path: exactly the facts B needs to answer.
    path, gap = _walk(st)
    un = set(_unsent(st))
    return [k for k in path if k in un], gap


def _tail_facts(st, gap):
    # Facts A holds beyond the gap: for the relations after the gap, prefer facts that link to another
    # fact A knows (a sub-chain office->city), since B may hold the missing hop and then needs these.
    if gap is None:
        return []
    known = _known(st)
    un = _unsent(st)
    idx = _CHAIN.index(gap[0])
    later = _CHAIN[idx + 1:]
    cands = []
    for k in un:
        if k[0] in later:
            linked = 0
            v = known.get(k)
            nxt = _CHAIN.index(k[0]) + 1
            if nxt < len(_CHAIN) and (_CHAIN[nxt], v) in known:
                linked = 1
            cands.append((-linked, _CHAIN.index(k[0]), un.index(k), k))
    cands.sort()
    return [c[3] for c in cands]


# chain_ask: compact form; one slot asks B for the hop A cannot resolve, the other sends A's next chain fact.
# B then sends that hop first, so the chain closes in the fewest rounds and tokens.
def chain_ask(st):
    facts, gap = _chain_facts(st)
    msg = [("#", "H")]
    if gap is not None:
        msg.append(("?", gap[0], gap[1]))
        rest = facts + _tail_facts(st, gap)
        if rest:
            msg.append(rest[0])
        return msg
    return msg + facts[:2] if facts else msg + _unsent(st)[:1]


# chain_compact: compact form with A's two most useful chain facts (path facts first, then tail facts beyond
# the gap); no question slot, for when B's standard ranking already finds the next hop.
def chain_compact(st):
    facts, gap = _chain_facts(st)
    rest = facts + _tail_facts(st, gap)
    if not rest:
        return None
    return [("#", "H")] + rest[:2]


# chain_sentences: the same chain-targeted facts as full sentences, in case the compact form is misread.
def chain_sentences(st):
    facts, gap = _chain_facts(st)
    rest = facts + _tail_facts(st, gap)
    if not rest:
        return None
    return rest[:2]


# route_gap: route by state. If A can already answer, send a single cheap compact fact (the episode ends this
# round anyway); if the gap is the first hop A lacks and A has no chain facts to share, ask and send the best
# tail fact; otherwise ask plus send the deepest chain fact (the one B can least derive).
def route_gap(st):
    facts, gap = _chain_facts(st)
    if gap is None:
        un = _unsent(st)
        return [("#", "H")] + (facts[-1:] if facts else un[:1])
    msg = [("#", "H"), ("?", gap[0], gap[1])]
    if facts:
        msg.append(facts[-1])
    else:
        tail = _tail_facts(st, gap)
        if tail:
            msg.append(tail[0])
    return msg


MOVES = {
    "chain_ask": chain_ask,
    "chain_compact": chain_compact,
    "chain_sentences": chain_sentences,
    "route_gap": route_gap,
}
