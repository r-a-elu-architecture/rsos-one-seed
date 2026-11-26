# RSOS R3 programs, domain 2: AI (agent_2) replying to a person in a real human-to-human conversation.
# Host = computer: VAKOG order V -> A -> K -> O -> G (U157).
#   V (see)    : the content words of the conversation, each with the trace of who said it and when (Law 1: words only).
#   O (trace)  : every word carries the traces of the turns it touched (U143): recency, speaker, both-speaker relation.
#   A (choose) : the room by state:  opening (fewer than 2 turns or no content in the person's message) ·
#                stable (a mid-length history) · overload (a long history: many input tokens) .
#   K (act)    : the room's chain: direct · MENTION (beam the landing words) · HOLO (hologram message U149/U154:
#                the compact whole state + the keys) · HOLOMIN (compress U8 to the minimal key).
#   G (result) : the reply's coverage of what the person says next.
# Golden light (U101): the best words are found by shared relations (words both speakers used, the person's own
# latest words); green particles (U102/U161) land only those words, at the place of need (the person's next turn).
# Laws: Law 0 (only words from the conversation itself; the program checks the room before it acts, else None),
# Law 1 (read scope: words only), Law 4 (land only words that change the next turn's coverage), Law 5 (relations
# raise the limit: the hologram sends the whole state compactly and the receiver derives the rest), Law 6
# (overload: compress, graceful loss of history instead of overflow).

import re

_STOP = set("""
a about above after again against all almost also although always am an and another any anybody anyone anything
anyway are aren't around as at away back be became because become been before being below between both but by can
can't cannot could couldn't did didn't do does doesn't doing don't done down during each either else enough even
ever every everyone everything few for from further get gets getting go goes going gone got gotten had hadn't has
hasn't have haven't having he he'd he'll he's her here here's hers herself him himself his how how's however i i'd
i'll i'm i've if in into is isn't it it's its itself just let let's like likely made make makes many may maybe me
might mine more most much must mustn't my myself near need needs neither never no nobody none nor not nothing now of
off often oh ok okay on once one only onto or other others otherwise ought our ours ourselves out over own perhaps
please put quite rather really right said same say says see seem seems shall shan't she she'd she'll she's should
shouldn't since so some somebody someone something sometimes somewhat soon still such sure take than that that's
the their theirs them themselves then there there's these they they'd they'll they're they've thing things think
this those though through thus to too toward towards under until up upon us use used very via want wants was wasn't
way we we'd we'll we're we've well were weren't what what's whatever when when's where where's whether which while
who who's whom whose why why's will with within without won't would wouldn't yes yet you you'd you'll you're you've
your yours yourself yourselves yeah yep nope hey hi hello hmm haha lol wow cool nice great good bad lot lots kind sort
pretty actually definitely probably absolutely totally anyway gonna wanna gotta know knew tell told thanks thank
day today time times year years also back first last next new old big little long feel felt
""".split())

_WORD = re.compile(r"[a-z][a-z']*[a-z]|[a-z]")


def _words(msg):
    out = []
    for w in _WORD.findall(str(msg).lower()):
        w = w.strip("'")
        if w.endswith("'s"):
            w = w[:-2]
        if len(w) >= 3 and w not in _STOP and not w.isdigit():
            out.append(w)
    return out


def _see(st):
    # V + O: each word with its traces (recency, speaker, relation between the two speakers)
    conv = list(st.get("conv") or [])
    if not conv:
        return None
    person = conv[-1][0]
    n = len(conv)
    score, by_person, by_other, first_pos = {}, set(), set(), {}
    total_words = 0
    for i, pair in enumerate(conv):
        spk, msg = pair[0], pair[1]
        total_words += len(str(msg).split())
        age = n - 1 - i
        w = 0.55 ** age
        if spk == person:
            w *= 1.6
        seen = set()
        for j, word in enumerate(_words(msg)):
            if word in seen:
                score[word] = score.get(word, 0.0) + 0.25 * w
                continue
            seen.add(word)
            score[word] = score.get(word, 0.0) + w
            first_pos.setdefault(word, (i, j))
            (by_person if spk == person else by_other).add(word)
    last = _words(conv[-1][1])
    return {"conv": conv, "person": person, "score": score, "by_person": by_person, "by_other": by_other,
            "last": last, "total_words": total_words, "first_pos": first_pos, "n": n}


def _golden(v, k, relation_bonus=0.6, last_bonus=1.0):
    # golden light U101: rank by shared relations (both speakers) and the person's own latest words
    last = set(v["last"])
    ranked = []
    for w, s in v["score"].items():
        r = s
        if w in v["by_person"] and w in v["by_other"]:
            r += relation_bonus
        if w in last:
            r += last_bonus
        ranked.append((-r, -len(w), w))
    ranked.sort()
    return [w for _, _, w in ranked[:k]]


def _room(v):
    # A: the state selects the protocol
    if v["n"] < 2 or len(v["last"]) < 2:
        return "opening"
    if v["total_words"] > 260:
        return "overload"
    return "stable"


# Program 1: golden_house
# Rooms: opening (fewer than 2 turns or the person's message has < 2 content words) -> direct ·
#        stable -> MENTION 4 golden words · overload (history > 260 words) -> HOLO with 6 golden words.
# Chain: V words -> O traces -> A room -> K MENTION | HOLO (green particles land the keys) -> G coverage.
# Laws: 0, 1, 4, 5 (overload: hologram instead of the whole history), 6.
# Invariant: every landed word occurs in the conversation · check: words drawn only from _words(conv).
def golden_house(st):
    v = _see(st)
    if v is None:
        return None
    room = _room(v)
    if room == "opening":
        return ("direct",)
    if room == "overload":
        ws = _golden(v, 6)
        return ("holo",) + tuple(ws) if ws else ("direct",)
    ws = _golden(v, 4)
    return ("mention",) + tuple(ws) if ws else ("direct",)


# Program 2: hologram_house
# Rooms: opening -> HOLO with the person's words · stable -> HOLO 6 golden words · overload (> 420 words) -> HOLOMIN.
# Chain: V -> O -> A -> K HOLO / COMPRESS(U8) to HOLOMIN -> G.  Laws: 1, 2 (structure sent, the model derives the
# values), 5 (send only the whole state's keys), 6.  Invariant: <= 6 words · check: len(words) <= 6.
def hologram_house(st):
    v = _see(st)
    if v is None:
        return None
    ws = _golden(v, 6)
    if not ws:
        return None
    if v["total_words"] > 420:
        return ("holomin",) + tuple(ws)
    return ("holo",) + tuple(ws)


# Program 3: tiger_person
# Tiger (U104, closest path): mention the 3 strongest words of the person's own current message (the place of need,
# U167); opening room (no content words) -> direct.
# Chain: V the person's message -> A -> K MENTION -> G.  Laws: 1 (read scope: the last turn first), 4.
# Invariant: the words come from the person's last message · check: subset of _words(conv[-1]).
def tiger_person(st):
    v = _see(st)
    if v is None:
        return None
    last = set(v["last"])
    if not last:
        return ("direct",)
    ws = [w for w in _golden(v, len(v["score"])) if w in last][:3]
    return ("mention",) + tuple(ws) if ws else ("direct",)


# Program 4: relation_beam
# Lion (U104, boldest path) along shared relations: mention up to 5 words that BOTH speakers used (the tube between
# the two spheres, U162), topped up with the person's latest words; opening -> direct.
# Chain: V -> O relation trace -> A -> K BEAM + MENTION -> G.  Laws: 4, 5 (relations raise the limit).
# Invariant: relation words first · check: words in by_person & by_other precede the rest.
def relation_beam(st):
    v = _see(st)
    if v is None:
        return None
    if _room(v) == "opening":
        return ("direct",)
    ranked = _golden(v, len(v["score"]), relation_bonus=1.5)
    shared = [w for w in ranked if w in v["by_person"] and w in v["by_other"]]
    rest = [w for w in ranked if w not in shared and w in set(v["last"])]
    ws = (shared + rest)[:5]
    return ("mention",) + tuple(ws) if ws else ("direct",)


# Program 5: holomin_key
# KEY (U110) + COMPRESS (U8): the minimal compact state with the 6 golden keys, every turn (fewest input tokens);
# opening (no content at all) -> None (the standard stays).
# Chain: V -> O -> K COMPRESS -> HOLOMIN -> G.  Laws: 2, 5, 6.  Invariant: <= 6 keys · check: len <= 6.
def holomin_key(st):
    v = _see(st)
    if v is None or not v["score"]:
        return None
    return ("holomin",) + tuple(_golden(v, 6))


MOVES = {
    "golden_house": golden_house,
    "hologram_house": hologram_house,
    "tiger_person": tiger_person,
    "relation_beam": relation_beam,
    "holomin_key": holomin_key,
}
