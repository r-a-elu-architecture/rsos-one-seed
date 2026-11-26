# RSOS decision programs, domain 2: AI replying to a person in a real conversation (CONF4, R1).
# Host = the conversation (a computer-run reply): V (see the whole conversation's words) -> A (the room by the
# conversation's state) -> K (compose the key words in order) -> O (trace: which words both speakers touched,
# which the person carried) -> G (the reply covers what the person says next).
# Pure functions of st; Python standard library only.

import re

_STOP = set("""
a about above after again against all also am an and any are aren't as at be because been before being below
between both but by can can't cannot could couldn't did didn't do does doesn't doing don't down during each few for
from further get got had hadn't has hasn't have haven't having he he'd he'll he's her here here's hers herself him
himself his how how's i i'd i'll i'm i've if in into is isn't it it's its itself just let's like me more most much
mustn't my myself no nor not now of off oh ok okay on once only or other ought our ours ourselves out over own really
same shan't she she'd she'll she's should shouldn't so some such than that that's the their theirs them themselves
then there there's these they they'd they'll they're they've this those through to too under until up us very was
wasn't we we'd we'll we're we've well were weren't what what's when when's where where's which while who who's whom
why why's will with won't would wouldn't yeah yes you you'd you'll you're you've your yours yourself yourselves
hi hello hey thanks thank lol haha one two thing things lot something anything everything nothing going gonna want
know think make made many even still yet back also though maybe sure great good nice cool right way day time
""".split())


def _words(text):
    return [w for w in re.findall(r"[a-z][a-z']+", str(text).lower()) if len(w) >= 3 and w not in _STOP
            and not w.endswith("'s")]


def _field(st):
    # V + O: every word with its trace: who touched it, how recently, how often (U143 the trace of every part)
    conv = list(st.get("conv") or [])
    if not conv:
        return [], {}, None, 0
    person = conv[-1][0]
    n = len(conv)
    info = {}
    total = 0
    for j, (spk, msg) in enumerate(conv):
        ws = _words(msg)
        total += len(str(msg).split())
        age = n - 1 - j
        for w in ws:
            d = info.setdefault(w, {"n": 0, "rec": 0.0, "spk": set(), "last": False, "first_j": j})
            d["n"] += 1
            d["rec"] = max(d["rec"], 1.0 / (1.0 + age))
            d["spk"].add(spk)
            if j == n - 1:
                d["last"] = True
    return conv, info, person, total


def _rank(info, person, mode):
    # K: compose the keys. Golden light (U101): best paths by shared relations = words both speakers touched;
    # Tiger (U104): the closest, precise path = the person's current message; Lion: the boldest = recurring themes.
    def score(w):
        d = info[w]
        s = d["rec"] * 2.0 + min(d["n"], 4) * 0.6
        if d["last"]:
            s += 2.5 if mode != "shared" else 1.5
        if len(d["spk"]) >= 2:
            s += 2.0 if mode == "shared" else 1.0
        if mode == "tiger" and not d["last"]:
            s -= 3.0
        return s
    return sorted(info, key=lambda w: (-score(w), w))


def _keys(st, k, mode):
    conv, info, person, total = _field(st)
    if not info:
        return [], total
    return _rank(info, person, mode)[:k], total


# house_route
# Rooms (triggered by the conversation's own size, read scope Law 1'): SEED (history <= 60 words: the full history
#   is cheap and holds everything) -> mention 4 keys | STABLE (61..300 words) -> mention 6 keys |
#   OVERLOAD (> 300 words) -> hologram reply: the compact whole state + 6 keys (U149/U154, compress U8).
# Chain (V->A->K->O->G): see every word and its trace -> room by size -> rank keys (Tiger: the person's current
#   message, golden light: words both speakers share) -> trace -> reply.
# Laws: Law 5 (send the receiver only what it cannot derive: keys, not the whole history, when the history is long),
#   Law 2 (structure = keys; the model writes the values), Law 1' (read only what is needed), Law 4 (no keys when
#   none exist: the direct reply), Law 0 (the reply stays inside the person's own words).
# Invariant: every key is a lowercase content word that occurs in the conversation so far.
# Check: overlap >= direct with fewer or equal tokens in the overload room.
def house_route(st):
    keys, total = _keys(st, 6, "mixed")
    if not keys:
        return ("direct",)
    if total <= 60:
        return ("mention",) + tuple(keys[:4])
    if total <= 300:
        return ("mention",) + tuple(keys[:6])
    return ("holo",) + tuple(keys[:6])


# holo_whole_state
# Rooms: EMPTY (no content word) -> direct | WHOLE (any other state) -> hologram message with the 6 strongest keys.
# Chain: see -> compress the conversation into its whole state (U8, U148) -> keys by shared relations (U101) ->
#   reply from the whole state (U149 hologram message) -> trace.
# Laws: Law 5 (relations raise the limit: the compact state + keys carry what the history carries), Law 2, Law 1'.
# Invariant: up to 6 keys, all from the conversation; fewer input tokens than direct.
# Check: overlap ~ direct at lower tokens.
def holo_whole_state(st):
    keys, total = _keys(st, 6, "shared")
    if not keys:
        return ("direct",)
    return ("holo",) + tuple(keys)


# holomin_seed
# Rooms: EMPTY -> direct | SEED (any other state) -> the minimal compact state with the 6 keys (the seed carries the
#   whole: U152 infinite seed; the smallest carrier, Law 5 at its limit).
# Chain: see -> keys (Tiger + Lion mixed) -> minimal hologram -> reply.
# Laws: Law 5, Law 2, Law 1' (fewest input tokens), Law 0.
# Invariant: fewest input tokens of all actions; keys from the conversation only.
# Check: overlap close to direct at the lowest token cost.
def holomin_seed(st):
    keys, total = _keys(st, 6, "mixed")
    if not keys:
        return ("direct",)
    return ("holomin",) + tuple(keys)


# mention_tiger
# Rooms: EMPTY -> direct | NEED (the person's current message holds content words) -> mention up to 5 of them,
#   ranked by their trace in the conversation (the Tiger's closest, precise path: U104); if the current message has
#   fewer than 3 keys the remaining slots take the strongest shared words (golden light, U101).
# Chain: see -> the person's current words -> rank by trace -> mention -> reply with the full history.
# Laws: Law 4 (land where the person's next message is formed: their current words), Law 1', Law 0.
# Invariant: keys are the person's own words first.
# Check: overlap >= direct at equal length budget.
def mention_tiger(st):
    conv, info, person, total = _field(st)
    if not info:
        return ("direct",)
    near = [w for w in _rank(info, person, "tiger") if info[w]["last"]][:5]
    if len(near) < 3:
        for w in _rank(info, person, "shared"):
            if w not in near:
                near.append(w)
            if len(near) >= 4:
                break
    if not near:
        return ("direct",)
    return ("mention",) + tuple(near)


# mention_golden_shared
# Rooms: EMPTY -> direct | SHARED (words touched by both speakers exist) -> mention up to 6 shared words, the
#   relations the two already hold in common (golden light U101, green particle landing on the shared relation U102) |
#   ALONE (no shared words) -> mention the person's 4 strongest current words (Tiger).
# Chain: see -> shared relations -> rank by recency and recurrence -> mention -> reply with the full history.
# Laws: Law 5 (relations raise the limit), Law 4 (landing on the shared relation), Law 1', Law 0.
# Invariant: keys are from the conversation; shared words first.
# Check: overlap >= direct.
def mention_golden_shared(st):
    conv, info, person, total = _field(st)
    if not info:
        return ("direct",)
    ranked = _rank(info, person, "shared")
    shared = [w for w in ranked if len(info[w]["spk"]) >= 2][:6]
    if len(shared) >= 2:
        if len(shared) < 4:
            for w in ranked:
                if w not in shared and info[w]["last"]:
                    shared.append(w)
                if len(shared) >= 4:
                    break
        return ("mention",) + tuple(shared)
    near = [w for w in _rank(info, person, "tiger") if info[w]["last"]][:4]
    if not near:
        near = ranked[:4]
    return ("mention",) + tuple(near)


MOVES = {
    "house_route": house_route,
    "holo_whole_state": holo_whole_state,
    "holomin_seed": holomin_seed,
    "mention_tiger": mention_tiger,
    "mention_golden_shared": mention_golden_shared,
}
