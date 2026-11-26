# RSOS decision programs, domain 3: two AI agents, A and B, answer one 4-hop question; we write A's message.
# Host = computer: V (see the chain manager -> team -> office -> city from X with what A holds) -> A (the room by
# the first hop A cannot resolve) -> K (compose the message slots in order) -> O (trace: what B already holds =
# sent_A and received) -> G (the first round with the right answer).
# Pure functions of st; Python standard library only.

HOPS = ("manager", "team", "office", "city")
H = ("#", "H")


def _k(x):
    return tuple(x) if isinstance(x, list) else x


def _walk(st):
    # V + O: walk the chain from X over everything A knows (its own facts + what B sent).
    # Returns: chain facts A holds that B does not yet hold (Law 5), the first unresolved hop (rel, subject) or None,
    # and whether A can already answer.
    mine = {_k(k): v for k, v in (st.get("mine") or {}).items()}
    recv = {_k(k): v for k, v in (st.get("received") or {}).items()}
    unsent = [_k(k) for k in (st.get("unsent") or [])]
    unsent_set = set(unsent)
    known = dict(mine)
    known.update(recv)
    s = st.get("x")
    to_send = []
    gap = None
    for rel in HOPS:
        key = (rel, s)
        if key in known:
            if key in mine and key in unsent_set and key not in recv:
                to_send.append(key)
            s = known[key]
        else:
            gap = key
            break
    return to_send, gap, unsent, gap is None


def _beyond(st, gap, limit):
    # Lion path past the gap: facts A holds for the NEXT relation whose subject appeared in any message so far
    # (U101 shared relations: a subject both sides have touched); used only to fill a slot that would otherwise go
    # to the standard's filler.
    if gap is None:
        return []
    i = HOPS.index(gap[0])
    if i + 1 >= len(HOPS):
        return []
    nxt = HOPS[i + 1]
    seen = set()
    for k, v in (st.get("received") or {}).items():
        seen.add(v)
        seen.add(_k(k)[1])
    out = []
    for k in st.get("unsent") or []:
        k = _k(k)
        if k[0] == nxt and k[1] in seen:
            out.append(k)
        if len(out) >= limit:
            break
    return out


# key_chain_house
# Rooms (A selects by the chain's state): WHOLE (A resolves the whole chain) -> compact message with the chain facts
#   B still lacks (both can answer this round) | GAP+FACTS (a hop A cannot resolve, A holds chain facts B lacks) ->
#   compact: the KEY question for the gap + the nearest chain fact (B's ranking then sends the gap's facts first) |
#   GAP ONLY (nothing of the chain to give) -> compact: the KEY + one Lion fact past the gap (or the standard filler).
# Chain (V->A->K->O->G): walk the chain -> room by the first gap -> key + facts in compact form -> trace of what B
#   holds -> answer.
# Laws: Law 5 (send only what B cannot derive from what it holds: never resend a received or sent fact), Law 2 (send
#   structure: the KEY rel(subject), B's runtime resolves its value), Law 1' (only chain facts are read and sent),
#   Law 4 (land at the place of need: the first unresolved hop, U161/U167), compress (U8: the compact form), Law 0.
# Invariant: every fact sent is on the resolved chain or is the key of the first gap.
# Check: right answer in no more rounds than the standard, at fewer tokens.
def key_chain_house(st):
    to_send, gap, unsent, whole = _walk(st)
    if whole:
        return [H] + to_send[:2]
    msg = [H, ("?", gap[0], gap[1])]
    if to_send:
        return msg + to_send[:1]
    return msg + _beyond(st, gap, 1)


# chain_facts_first
# Rooms: FACTS (A holds chain facts B lacks) -> compact message with the 2 nearest of them (B, holding them, walks
#   the chain itself and its ranking sends the next subjects' facts) | GAP ONLY -> the KEY for the gap + Lion fact |
#   WHOLE -> the chain facts B lacks, compact.
# Chain: walk -> give the structure B lacks first (beam down the chain) -> key only when nothing is left to give.
# Laws: Law 5, Law 2 (key), Law 4, compress (U8), Law 0.
# Invariant: at most 2 slots; chain facts before questions.
# Check: right answer, fewer tokens than the standard.
def chain_facts_first(st):
    to_send, gap, unsent, whole = _walk(st)
    if to_send:
        return [H] + to_send[:2]
    if gap is not None:
        return [H, ("?", gap[0], gap[1])] + _beyond(st, gap, 1)
    return [H]


# key_twin_question
# Rooms: GAP -> compact: the KEY + the nearest chain fact; when A has no chain fact to give, the KEY + the next hop
#   past the gap read by shared relations | WHOLE -> compact chain facts.
# Chain: as key_chain_house, but the chain fact chosen is the one CLOSEST to the gap (Tiger, U104: the precise path:
#   the fact B needs to continue from where the key lands) instead of the nearest to X.
# Laws: Law 5, Law 2, Law 4 (landing at the gap), Law 1', Law 0.
# Invariant: the key always names the first unresolved hop.
# Check: right answer at fewer rounds and tokens than the standard.
def key_twin_question(st):
    to_send, gap, unsent, whole = _walk(st)
    if whole:
        return [H] + to_send[-2:]
    msg = [H, ("?", gap[0], gap[1])]
    if to_send:
        return msg + to_send[-1:]
    return msg + _beyond(st, gap, 1)


# chain_sentences
# Rooms: FACTS -> the 2 nearest chain facts B lacks, as full sentences (the host's native carrier) | NONE -> the
#   standard's own choice (None: the program does not apply).
# Chain: walk -> give the chain structure B lacks -> sentences.
# Laws: Law 5 (only what B cannot derive), Law 1' (only the chain), Law 4, Law 0.
# Invariant: never sends a fact B already holds.
# Check: right answer at least as often as the standard.
def chain_sentences(st):
    to_send, gap, unsent, whole = _walk(st)
    return to_send[:2] if to_send else None


# hologram_key_both
# Rooms: GAP with >= 2 chain facts to give -> compact: the 2 facts (B can continue the whole chain) |
#   GAP with <= 1 -> compact: the KEY + that fact | WHOLE -> compact chain facts | round >= 3 (deficit of rounds,
#   U103) -> always the KEY when a gap remains (the place of need first).
# Chain: walk -> route by state (facts vs key) -> compact -> answer.
# Laws: Law 5, Law 2, Law 4, P9 complementation (each side serves the hop it holds), compress (U8), Law 0.
# Invariant: at most 2 slots; every fact on the chain.
# Check: right answer, fewer tokens than the standard.
def hologram_key_both(st):
    to_send, gap, unsent, whole = _walk(st)
    if whole:
        return [H] + to_send[:2]
    late = (st.get("t", 0) or 0) >= 3
    if len(to_send) >= 2 and not late:
        return [H] + to_send[:2]
    msg = [H, ("?", gap[0], gap[1])]
    if to_send:
        return msg + to_send[:1]
    return msg + _beyond(st, gap, 1)


MOVES = {
    "key_chain_house": key_chain_house,
    "chain_facts_first": chain_facts_first,
    "key_twin_question": key_twin_question,
    "chain_sentences": chain_sentences,
    "hologram_key_both": hologram_key_both,
}
