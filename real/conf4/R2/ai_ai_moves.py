# RSOS R2 programs, domain 3: two AI agents, A and B, answer one 4-hop question; A's message per round.
# Host = computer: V -> A -> K -> O -> G (U157):
#   V (see)     walk the question's chain manager -> team -> office -> city from X over mine + received
#   A (choose)  the chain state selects the room: resolved / blocked at a hop / blocked with nothing to give
#   K (act)     the message: the chain facts B cannot derive (Law 5) and a KEY for the hop A cannot resolve
#   O (trace)   sent_A / received: never resend what B already holds
#   G (result)  the city
# Pure functions of `st`; standard library only.

CHAIN = ("manager", "team", "office", "city")


def _k(key):
    try:
        return tuple(key)
    except TypeError:
        return key


# ---------------------------------------------------------------- V: see (the chain, with its trace)
def _see(st):
    x = st.get("x")
    mine = {_k(k): v for k, v in (st.get("mine") or {}).items()}
    recv = {_k(k): v for k, v in (st.get("received") or {}).items()}
    unsent_raw = list(st.get("unsent") or [])
    unsent = {_k(k): k for k in unsent_raw}  # normalised -> original key object
    known = dict(mine)
    known.update(recv)
    subj = x
    give = []          # chain facts A holds and has not sent (B cannot derive them)
    missing = None     # the first hop A cannot resolve: (rel, subject)
    resolved = 0
    for rel in CHAIN:
        key = (rel, subj)
        if key in known:
            if key in unsent:
                give.append(unsent[key])
            subj = known[key]
            resolved += 1
        else:
            missing = key
            break
    return {"give": give, "missing": missing, "resolved": resolved, "unsent": unsent_raw}


def _room(v):
    if v["missing"] is None:
        return "resolved"     # A can answer now: land the least, compactly
    if v["give"]:
        return "blocked_give"  # A holds chain facts B needs and lacks one hop
    return "blocked_ask"       # A has nothing on the chain to give: ask for the hop


# ---------------------------------------------------------------- Program 1
# house_chain_key
# Rooms (trigger -> chain):
#   resolved     (all 4 hops known)              -> [#H, chain facts]            (answer this round; fewest tokens)
#   blocked_give (hop i unknown, chain facts held) -> [#H, ?(rel_i, subj_i), nearest chain fact]
#   blocked_ask  (hop i unknown, nothing to give) -> [#H, ?(rel_i, subj_i)]
# Chain: V walk the chain -> A room -> K compress (U8, "#H") + KEY (U110, Law 2: send the structure, B's
#   runtime ranking resolves the value) + green particle at the place of need (U102/U167: the blocked hop)
#   -> O never resend (sent_A) -> G city.
# Laws: Law 2 (blind: a key, not a value), Law 5 (send only what B cannot derive: A's own chain facts),
#   Law 4 (land at the one hop that changes the episode's future), Law 1 (read scope: only the 4 chain keys),
#   Law 0 (every key comes from st["unsent"]; at most 2 slots).
# Invariant + check: every fact sent lies on the question's chain and is in unsent; the key names the first
#   unresolved hop (check: walk from X over mine+received stops exactly there).
def house_chain_key(st):
    v = _see(st)
    room = _room(v)
    if room == "resolved":
        return [("#", "H")] + v["give"][:2]
    q = ("?", v["missing"][0], v["missing"][1])
    if room == "blocked_give":
        return [("#", "H"), q, v["give"][-1]]
    return [("#", "H"), q]


# ---------------------------------------------------------------- Program 2
# chain_key_first
# Rooms: as house_chain_key, but blocked_give sends the FIRST chain fact (Lion, U104: start of the path,
#   the boldest anchor from X) with the key.
# Chain: V -> A -> K compress + key + beam from the root -> O -> G.
# Laws: Law 2, Law 5, Law 4, Law 1, Law 0.
# Invariant + check: as house_chain_key.
def chain_key_first(st):
    v = _see(st)
    room = _room(v)
    if room == "resolved":
        return [("#", "H")] + v["give"][:2]
    q = ("?", v["missing"][0], v["missing"][1])
    if room == "blocked_give":
        return [("#", "H"), q, v["give"][0]]
    return [("#", "H"), q]


# ---------------------------------------------------------------- Program 3
# chain_compact
# Rooms:
#   A holds unsent chain facts -> [#H, up to 2 chain facts] (no key; B's own ranking fills the hop)
#   otherwise                  -> [#H, ?(missing hop)] if a hop is missing, else [#H]
# Chain: V -> A -> K compress (U8) -> O -> G.
# Laws: Law 5 (only facts B cannot derive), Law 1, Law 0.
# Invariant + check: every fact sent is on the chain and unsent.
def chain_compact(st):
    v = _see(st)
    if v["give"]:
        return [("#", "H")] + v["give"][:2]
    if v["missing"] is not None:
        return [("#", "H"), ("?", v["missing"][0], v["missing"][1])]
    return [("#", "H")]


# ---------------------------------------------------------------- Program 4
# chain_sentences
# Rooms:
#   A holds unsent chain facts -> [up to 2 chain facts] as sentences
#   otherwise                  -> None (the standard)
# Chain: V -> A -> K land the chain facts in the receiver's own (sentence) channel -> G.
# Laws: Law 5, Law 4, Law 0 (the host's native form is kept; only the selection changes: Law 3,
#   repair only the part that differs from the standard).
# Invariant + check: every fact sent is on the chain and unsent.
def chain_sentences(st):
    v = _see(st)
    if v["give"]:
        return list(v["give"][:2])
    return None


# ---------------------------------------------------------------- Program 5
# chain_key_twice
# Rooms:
#   blocked (any)  -> [#H, ?(missing hop), nearest chain fact or nothing]
#   resolved       -> [#H, chain facts]
#   with the trace: if the key for this same hop was already asked in an earlier round and B still did not
#   answer it (the hop is still missing at round >= 1) and A still holds >= 2 unsent chain facts, both slots
#   carry those facts so that B can finish the chain itself (P9 complementation: each side serves the hops
#   it holds); otherwise the key is sent again with the nearest chain fact.
# Chain: V -> A -> K key + compress -> O trace of rounds -> G.
# Laws: Law 2, Law 5, Law 4, Law 0.
# Invariant + check: as house_chain_key.
def chain_key_twice(st):
    v = _see(st)
    room = _room(v)
    if room == "resolved":
        return [("#", "H")] + v["give"][:2]
    q = ("?", v["missing"][0], v["missing"][1])
    if int(st.get("t", 0)) >= 1 and len(v["give"]) >= 2:
        return [("#", "H")] + v["give"][:2]
    if v["give"]:
        return [("#", "H"), q, v["give"][-1]]
    return [("#", "H"), q]


MOVES = {
    "house_chain_key": house_chain_key,
    "chain_key_first": chain_key_first,
    "chain_compact": chain_compact,
    "chain_sentences": chain_sentences,
    "chain_key_twice": chain_key_twice,
}
