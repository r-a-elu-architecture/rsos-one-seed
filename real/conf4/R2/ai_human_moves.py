# RSOS R2 programs, domain 2: AI replying to a person in a human-to-human conversation.
# Host = computer: V -> A -> K -> O -> G (U157):
#   V (see)     the conversation's words, per speaker, with recency
#   A (choose)  the heard state selects the room (route by state, U5/U64/U69)
#   K (act)     build the reply action: which channel (direct / mention / holo / holomin) and which keys
#   O (trace)   every word carries the trace of who said it and when (U143, U160 letter address)
#   G (result)  the reply that lands on what the person says next
# The keys are chosen by golden light (U101): words on the shared relations of both speakers, weighted
# to the person and to the present. Pure functions of `st`; standard library only.

import re

_STOP = set("""
a about above after again against all almost also am an and any are aren as at be because been before being
below between both but by can cannot could couldn did didn do does doesn doing don down during each else even
ever every few for from further get gets got had hadn has hasn have haven having he her here hers herself him
himself his how however i if in into is isn it its itself just know let like ll lot me might more most much must
my myself need no nor not now of off oh ok okay on once one only or other our ours ourselves out over own pretty
quite re really right said same say says she should shouldn so some something still such sure than that thats the
their theirs them themselves then there these they thing things think this those though through to too
under until up us ve very was wasn way we well were weren what when where which while who whom why will with
won would wouldn yeah yes yet you your yours yourself yourselves going want go thank thanks hey hi hello
lol haha great good nice cool also gonna wanna maybe kind sort bit actually anyway
""".split())


def _words(msg):
    out = []
    for w in re.findall(r"[a-z][a-z']*", str(msg).lower()):
        w = w.strip("'")
        if w.endswith("'s"):
            w = w[:-2]
        if len(w) >= 3 and w not in _STOP and "'" not in w:
            out.append(w)
    return out


# ---------------------------------------------------------------- V: see (with the O trace)
def _see(st):
    conv = list(st.get("conv") or [])
    if not conv:
        return None
    person = conv[-1][0]
    per_msg = [(spk, _words(m), str(m)) for spk, m in conv]
    n_words = sum(len(str(m).split()) for _, m in conv)
    return {"conv": conv, "person": person, "msgs": per_msg, "n_words": n_words,
            "last": per_msg[-1], "t": int(st.get("t", 0))}


def _golden(v, k, decay=0.75, horizon=None):
    # golden light (U101): score = recency (present > past) x speaker (the person) x shared relation (both speakers)
    msgs = v["msgs"] if horizon is None else v["msgs"][-horizon:]
    score, speakers, first = {}, {}, {}
    n = len(msgs)
    for i, (spk, ws, _) in enumerate(msgs):
        rec = decay ** (n - 1 - i)
        wt = rec * (1.6 if spk == v["person"] else 1.0)
        for w in set(ws):
            score[w] = score.get(w, 0.0) + wt * (1.0 + 0.25 * (ws.count(w) - 1))
            speakers.setdefault(w, set()).add(spk)
            first.setdefault(w, i)
    for w in score:
        if len(speakers[w]) >= 2:
            score[w] *= 1.5  # shared relation between the two speakers
    ranked = sorted(score, key=lambda w: (-score[w], first[w], w))
    return ranked[:k]


def _tiger(v, k):
    # Tiger (U104): the closest, precise path = the person's current message, in its own order
    seen, out = set(), []
    for w in v["last"][1]:
        if w not in seen:
            seen.add(w)
            out.append(w)
    # longer (more specific) words first, ties by order of appearance
    out = sorted(out, key=lambda w: (-min(len(w), 8), out.index(w)))
    return out[:k]


def _merge(*lists, k=6):
    out = []
    for L in lists:
        for w in L:
            if w not in out:
                out.append(w)
    return out[:k]


# ---------------------------------------------------------------- A: choose the room
def _room(v):
    if v["n_words"] > 260:
        return "overload"      # history heavy: compress the whole into a hologram
    if len(v["last"][1]) < 3:
        return "deficit"       # the person's message carries little: land from the whole trace
    if "?" in v["last"][2]:
        return "uncertainty"   # the person asks: answer on their own words first
    return "stable"


# ---------------------------------------------------------------- Program 1
# house_vakog
# Rooms (trigger -> chain):
#   overload    (history > 260 words)        -> holomin(6 golden words)   [U149 hologram, U8 compress, Law 5, Law 1]
#   deficit     (<3 content words now)        -> mention(4 golden words over the whole conversation)
#                                                 [U102/U167 green particle at the place of need, U103]
#   uncertainty (the person asks, "?")        -> mention(4 Tiger words of the question + 2 golden)  [U104 Tiger]
#   stable                                    -> holo(6 golden words)     [U149, Law 5]
# Chain: V see words + O trace -> A room -> K channel + keys -> G reply.
# Laws: Law 5 (send only what the receiver cannot derive: a compact whole + keys), Law 1 (read scope),
#   Law 4 (the keys land where the next message will be), Law 0 (only words from the conversation; never empty).
# Invariant + check: every key is a lowercase content word of the conversation so far (check: drawn from _words);
#   at most 6 keys; if no key exists the program returns None (the standard reply).
def house_vakog(st):
    v = _see(st)
    if v is None:
        return None
    room = _room(v)
    if room == "overload":
        ws = _golden(v, 6)
        return ("holomin",) + tuple(ws) if ws else None
    if room == "deficit":
        ws = _golden(v, 4)
        return ("mention",) + tuple(ws) if ws else None
    if room == "uncertainty":
        ws = _merge(_tiger(v, 4), _golden(v, 6), k=6)
        return ("mention",) + tuple(ws) if ws else None
    ws = _golden(v, 6)
    return ("holo",) + tuple(ws) if ws else None


# ---------------------------------------------------------------- Program 2
# holomin_golden
# Rooms: one room for every state (the zoom-invariant rule): holomin with 6 golden words.
# Chain: V -> O trace -> K compress (U8) -> hologram minimal (U149) -> G.
# Laws: Law 2 (structure/keys sent, the model computes the words), Law 5, Law 1 (fewest input tokens).
# Invariant + check: input = minimal compact state; keys <= 6 and from the conversation.
def holomin_golden(st):
    v = _see(st)
    if v is None:
        return None
    ws = _golden(v, 6)
    return ("holomin",) + tuple(ws) if ws else None


# ---------------------------------------------------------------- Program 3
# holo_golden
# Rooms: one room: holo (the whole state as a compact hologram) with 6 golden words.
# Chain: V -> O -> K compress -> hologram (U149/U154) -> G.
# Laws: Law 5, Law 1, Law 0.
# Invariant + check: keys <= 6, all from the conversation.
def holo_golden(st):
    v = _see(st)
    if v is None:
        return None
    ws = _golden(v, 6)
    return ("holo",) + tuple(ws) if ws else None


# ---------------------------------------------------------------- Program 4
# mention_tiger
# Rooms:
#   the person's message has content words -> mention(Tiger words of the current message + golden to 5)
#   otherwise                              -> mention(5 golden words)
# Chain: V -> A -> K beam (Tiger, U104: the closest precise path) -> G.
# Laws: Law 4 (land on the person's own words, where the next message continues), Law 1, Law 0.
# Invariant + check: keys <= 5, drawn from the conversation; the history channel is kept (direct context).
def mention_tiger(st):
    v = _see(st)
    if v is None:
        return None
    ws = _merge(_tiger(v, 3), _golden(v, 5), k=5)
    return ("mention",) + tuple(ws) if ws else None


# ---------------------------------------------------------------- Program 5
# mention_lion
# Rooms: one room: mention(6 golden words over the last 6 messages) with the full history.
# Chain: V -> O trace -> K beam (Lion, U2/U104: the boldest path, the widest set of keys) -> G.
# Laws: Law 4, Law 5 (shared relations of both speakers weighted up), Law 0.
# Invariant + check: keys <= 6, all from the last 6 messages.
def mention_lion(st):
    v = _see(st)
    if v is None:
        return None
    ws = _golden(v, 6, horizon=6)
    return ("mention",) + tuple(ws) if ws else None


MOVES = {
    "house_vakog": house_vakog,
    "holomin_golden": holomin_golden,
    "holo_golden": holo_golden,
    "mention_tiger": mention_tiger,
    "mention_lion": mention_lion,
}
