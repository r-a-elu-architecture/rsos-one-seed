# RSOS R3 programs, domain 3: two AI agents, A and B, answer one multi-hop question; A's message each round.
# Host = computer: VAKOG order V -> A -> K -> O -> G (U157).
#   V (see)    : walk the question's chain from X over what A holds and what B has sent (mine + received).
#   O (trace)  : which hops are A's own, which came from B, which A already sent (sent_A / unsent).
#   A (choose) : the room by state:
#                landed  : A already holds the whole chain (it answers this round) -> minimal compact message
#                deficit : a hop A cannot resolve (the lack, U103) -> a KEY for that hop (B holds it)
#                prefix  : A's own resolved hops B does not yet have -> send them so B can walk the chain too
#   K (act)    : compact form ("#", "H") = compress U8; KEY ("?", rel, subject) = U110 key; the facts = green
#                particles landed at the place of need (U102/U161/U167).
#   G (result) : the first round in which A or B can answer.
# Laws: Law 0 (only keys from unsent are sent; the program checks every key before it lands, else None),
# Law 1 (read scope: only the chain's hops), Law 2 (blind: the key is structure only, B's runtime ranking computes
# the values it returns), Law 4 (land only facts that change the episode's future: chain facts, never distractors;
# withholding is a move), Law 5 (send only what B cannot derive from what it holds: A's own hops, never facts B sent),
# golden light U101 (the next fact is found by shared relations: subjects already named in the chain).

import re

_DEFAULT_CHAIN = ["manager", "team", "office", "city"]


def _chain_rels(st):
    q = str(st.get("question") or "")
    inner = re.findall(r"the (\w+) of", q)
    m = re.search(r"[Ii]n which (\w+)", q)
    if inner and m:
        rels = list(reversed(inner)) + [m.group(1)]
        if all(isinstance(r, str) for r in rels):
            return rels
    return list(_DEFAULT_CHAIN)


def _key(k):
    return tuple(k) if isinstance(k, (list, tuple)) else k


def _see(st):
    # V + O: walk the chain over mine + received; record each hop's holder
    mine = {_key(k): v for k, v in (st.get("mine") or {}).items()}
    recv = {_key(k): v for k, v in (st.get("received") or {}).items()}
    unsent = list(st.get("unsent") or [])
    unsent_map = {_key(k): k for k in unsent}
    rels = _chain_rels(st)
    subj = st.get("x")
    path, gap = [], None
    for rel in rels:
        k = (rel, subj)
        if k in mine:
            path.append((k, "A"))
            subj = mine[k]
        elif k in recv:
            path.append((k, "B"))
            subj = recv[k]
        else:
            gap = k
            break
    return {"mine": mine, "recv": recv, "unsent": unsent, "unsent_map": unsent_map, "rels": rels,
            "path": path, "gap": gap}


def _prefix_unsent(v):
    # A's own hops on the resolved path that B does not hold yet (Law 5), in chain order
    return [v["unsent_map"][k] for k, who in v["path"] if who == "A" and k in v["unsent_map"]]


def _golden_candidates(v, exclude):
    # golden light U101: own unsent facts whose relation lies after the gap and whose subject is already named
    if v["gap"] is None:
        return []
    named = set()
    for k, _ in v["path"]:
        named.add(k[1])
    for val in list(v["recv"].values()) + [v["mine"][k] for k, w in v["path"] if w == "A"]:
        named.add(val)
    later = v["rels"][v["rels"].index(v["gap"][0]) + 1:] if v["gap"][0] in v["rels"] else []
    out = []
    for k in v["unsent"]:
        kk = _key(k)
        if kk in exclude or not isinstance(kk, tuple) or len(kk) != 2:
            continue
        if kk[0] in later and kk[1] in named:
            out.append(k)
    return out


def _compact(items):
    return [("#", "H")] + list(items)


# Program 1: key_prefix_house
# Rooms: landed (whole chain held) -> compact, the chain facts B lacks (or nothing: the standard fills) ·
#        deficit (a gap) -> KEY for the gap hop + 1 own prefix fact (else a golden-light candidate) ·
#        no gap and nothing to send -> compact message.
# Chain: V walk -> O holders -> A room -> K COMPRESS + KEY + LAND(prefix) -> G.
# Laws: 0, 1, 2 (key = structure only), 4, 5.
# Invariant: every fact sent is A's own and unsent, at most 2 slots · check: keys drawn from st["unsent"] only.
def key_prefix_house(st):
    v = _see(st)
    if st.get("x") is None:
        return None
    prefix = _prefix_unsent(v)
    if v["gap"] is None:                                   # landed: A answers this round
        return _compact(prefix[:2])
    rel, subj = v["gap"]
    second = prefix[:1] or _golden_candidates(v, set())[:1]
    return _compact([("?", rel, subj)] + second)


# Program 2: lion_prefix_house
# Lion (U104, boldest path): first carry B along the chain: 2 own prefix facts B lacks (B can then walk the chain on
# its own half and answer); the KEY only when fewer than 2 prefix facts remain.
# Rooms: landed -> compact prefix · prefix (>= 2 own unsent hops) -> 2 facts · deficit -> KEY + 1 fact.
# Chain: V -> O -> A -> K BEAM(prefix) -> KEY -> G.  Laws: 0, 4, 5.
# Invariant: prefix facts in chain order · check: facts sent follow the walk from X.
def lion_prefix_house(st):
    v = _see(st)
    if st.get("x") is None:
        return None
    prefix = _prefix_unsent(v)
    if v["gap"] is None or len(prefix) >= 2:
        return _compact(prefix[:2])
    rel, subj = v["gap"]
    return _compact([("?", rel, subj)] + prefix[:1] + _golden_candidates(v, set())[:1 - len(prefix[:1])])


# Program 3: tiger_key
# Tiger (U104, closest precise path): the KEY for the gap and, in the second slot, a golden-light candidate (a fact
# on a later hop whose subject is already named), else the prefix; landed -> compact prefix.
# Chain: V -> A -> K KEY -> LAND(candidate) -> G.  Laws: 1, 2, 4, 5.
# Invariant: one key per message at most · check: exactly one ("?", ...) when a gap exists.
def tiger_key(st):
    v = _see(st)
    if st.get("x") is None:
        return None
    prefix = _prefix_unsent(v)
    if v["gap"] is None:
        return _compact(prefix[:2])
    rel, subj = v["gap"]
    second = _golden_candidates(v, set())[:1] or prefix[:1]
    return _compact([("?", rel, subj)] + second)


# Program 4: sentence_prefix
# The same chain landing as plain sentences (no compact form): own prefix facts B lacks, then golden-light
# candidates; None when A has nothing on the chain to give (the standard stays: Law 4 withholding).
# Chain: V -> O -> K LAND(prefix as sentences) -> G.  Laws: 0, 4, 5.
# Invariant: chain facts only · check: every key is a path hop or a later-hop candidate.
def sentence_prefix(st):
    v = _see(st)
    if st.get("x") is None:
        return None
    items = _prefix_unsent(v)
    if len(items) < 2:
        items = items + [k for k in _golden_candidates(v, set()) if k not in items]
    items = items[:2]
    return items if items else None


MOVES = {
    "key_prefix_house": key_prefix_house,
    "lion_prefix_house": lion_prefix_house,
    "tiger_key": tiger_key,
    "sentence_prefix": sentence_prefix,
}
