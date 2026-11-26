# Domain 3: A's message in a two-agent 4-hop question (C3).
# Chain: X -manager-> M -team-> T -office-> O -city-> answer. Walk the chain over A's facts plus what B sent;
# send only on-chain facts B lacks, in compact form, and ask B for the first hop A cannot resolve.

HOPS = ("manager", "team", "office", "city")


def _k(key):
    return tuple(key)


def _walk(st):
    # returns (chain_keys_known, blocked_key or None)
    known = {}
    known.update({_k(k): v for k, v in st["mine"].items()})
    known.update({_k(k): v for k, v in st["received"].items()})
    cur = st["x"]
    keys = []
    for rel in HOPS:
        key = (rel, cur)
        if key in known:
            keys.append(key)
            cur = known[key]
        else:
            return keys, key
    return keys, None


def _unsent(st):
    return [_k(k) for k in st["unsent"]]


def _chain_to_send(st):
    keys, blocked = _walk(st)
    uns = set(_unsent(st))
    return [k for k in keys if k in uns], blocked


def _speculative(st, blocked, exclude):
    # facts that could lie beyond the block: A's unsent facts of the later hop relations,
    # preferring subjects B has already mentioned (values in received)
    uns = [k for k in _unsent(st) if k not in exclude]
    if blocked is None:
        return []
    idx = HOPS.index(blocked[0])
    later = HOPS[idx + 1:]
    seen_vals = set(str(v) for v in st["received"].values()) | set(str(k[1]) for k in st["received"])
    cands = [k for k in uns if k[0] in later]
    cands.sort(key=lambda k: (0 if str(k[1]) in seen_vals else 1, later.index(k[0])))
    return cands


# chain_ask: compact; when the chain is blocked at a hop B holds, ask for it (B then sends that subject first)
# plus A's most useful on-chain fact; when unblocked, send the 2 on-chain facts B lacks.
def chain_ask(st):
    send, blocked = _chain_to_send(st)
    if blocked is not None:
        extra = send[:1] or _speculative(st, blocked, set())[:1]
        return [("#", "H"), ("?", blocked[0], blocked[1])] + extra
    msg = send[:2]
    if len(msg) < 2:
        return [("#", "H")] + msg if msg else [("#", "H")]
    return [("#", "H")] + msg


# chain_push: compact, no question: the 2 on-chain facts B lacks, else facts that may extend B's side of
# the chain (later-hop relations, subjects B has mentioned). Cheapest full-fact payload.
def chain_push(st):
    send, blocked = _chain_to_send(st)
    msg = send[:2]
    if len(msg) < 2:
        msg += _speculative(st, blocked, set(msg))[: 2 - len(msg)]
    return [("#", "H")] + msg


# chain_sentences: same selection as chain_push but as full sentences (if the model reads prose more reliably).
def chain_sentences(st):
    send, blocked = _chain_to_send(st)
    msg = send[:2]
    if len(msg) < 2:
        msg += _speculative(st, blocked, set(msg))[: 2 - len(msg)]
    return msg if msg else None


# ask_first_round_then_push: round 0 sends the chain head and asks for the first blocked hop; later rounds
# re-ask only if B has not resolved it yet, otherwise push remaining chain facts.
def ask_then_push(st):
    send, blocked = _chain_to_send(st)
    if blocked is not None and (st["t"] == 0 or not send):
        extra = send[:1] or _speculative(st, blocked, set())[:1]
        return [("#", "H"), ("?", blocked[0], blocked[1])] + extra
    msg = send[:2]
    if len(msg) < 2:
        msg += _speculative(st, blocked, set(msg))[: 2 - len(msg)]
    return [("#", "H")] + msg


MOVES = {
    "chain_ask": chain_ask,
    "chain_push": chain_push,
    "chain_sentences": chain_sentences,
    "ask_then_push": ask_then_push,
}
