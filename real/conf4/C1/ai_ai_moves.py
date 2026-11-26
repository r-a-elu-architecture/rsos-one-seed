# Domain 3: two agents answer a 4-hop question; A's message. Programs follow the question's chain.

CHAIN = ("manager", "team", "office", "city")


def _k(key):
    return tuple(key) if isinstance(key, (list, tuple)) else key


def _walk(st):
    """Walk X -manager-> M -team-> T -office-> O -city-> C over A's known facts.
    Returns (chain_keys_known, gap) where gap = (rel, subject) of the first unknown hop, or None."""
    known = {}
    for d in (st.get("mine") or {}, st.get("received") or {}):
        for key, v in d.items():
            known[_k(key)] = v
    cur, keys = st.get("x"), []
    for rel in CHAIN:
        key = (rel, cur)
        if key in known:
            keys.append(key)
            cur = known[key]
        else:
            return keys, key
    return keys, None


def _chain_unsent(st):
    """A's own unsent facts lying on the resolved prefix of the chain (B needs these to traverse)."""
    keys, gap = _walk(st)
    unsent = list(st.get("unsent") or [])
    lookup = {_k(u): u for u in unsent}
    return [lookup[k] for k in keys if k in lookup], gap


def _subject_facts(st, subj, exclude):
    """A's unsent facts about a given subject on the chain relations (useful lookahead)."""
    out = []
    for u in st.get("unsent") or []:
        ku = _k(u)
        if ku[1] == subj and ku[0] in CHAIN and u not in exclude:
            out.append(u)
    return out


# chain_ask: compact message = a question for the first hop A cannot resolve (B holds it and answers it
# first) + A's next unsent chain fact, so B can walk the prefix and A gets the missing hop in the same round.
def chain_ask(st):
    facts, gap = _chain_unsent(st)
    if gap is None:
        return [("#", "H")] + facts[:2] if facts else None
    msg = [("#", "H"), ("?", gap[0], gap[1])]
    if facts:
        msg.append(facts[0])
    return msg


# chain_push: compact message carrying two of A's chain-prefix facts (B can then traverse past them with its
# own holdings); when fewer than two remain, the free slot becomes a question for the missing hop.
def chain_push(st):
    facts, gap = _chain_unsent(st)
    if len(facts) >= 2:
        return [("#", "H")] + facts[:2]
    if gap is not None:
        msg = [("#", "H"), ("?", gap[0], gap[1])]
        return msg + facts[:1]
    return [("#", "H")] + facts if facts else None


# chain_sentences: the same chain-prefix facts as full sentences (for a B that reads sentences more reliably);
# only applies when A holds unsent chain facts.
def chain_sentences(st):
    facts, gap = _chain_unsent(st)
    return facts[:2] if facts else None


# ask_lookahead: question for the missing hop + the last known chain fact; if nothing is left to send on the
# prefix, add A's fact about the gap subject on another chain relation (lookahead for the hop after the gap).
def ask_lookahead(st):
    facts, gap = _chain_unsent(st)
    if gap is None:
        return chain_ask(st)
    msg = [("#", "H"), ("?", gap[0], gap[1])]
    if facts:
        msg.append(facts[-1])
    else:
        extra = _subject_facts(st, gap[1], [])
        if extra:
            msg.append(extra[0])
    return msg


MOVES = {
    "chain_ask": chain_ask,
    "chain_push": chain_push,
    "chain_sentences": chain_sentences,
    "ask_lookahead": ask_lookahead,
}
