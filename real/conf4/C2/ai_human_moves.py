# Domain 2: AI replying to a person in a human-to-human conversation. Pure functions of `st`.
import re

_STOP = set("""
a about above after again against all also am an and any are aren as at be because been before being below between
both but by can cannot could did didn do does doesn doing don down during each few for from further get got had has
have having he her here hers herself him himself his how i if in into is isn it its itself just let ll me more most
much my myself no nor not now of off on once only or other ought our ours ourselves out over own re same she should so
some such than that the their theirs them themselves then there these they this those through to too under until up
us very was we were what when where which while who whom why will with would you your yours yourself yourselves
yes yeah okay ok oh hi hello hey well really like know think going go im ive youre dont thats its lot one thing things
something anything nothing maybe sure good great nice cool right lol haha want make way say said see sounds
near last ever even still always never though thanks thank pretty kind gonna wanna yep nope
""".split())


def _words(text):
    return [w for w in re.findall(r"[a-z]+", str(text).lower()) if len(w) >= 3 and w not in _STOP]


def _person(st):
    conv = st.get("conv") or []
    return conv[-1][0] if conv else None


def _rank(st, person_weight=1.6, recency=0.75, last_bonus=2.0):
    # Score content words by recency-weighted frequency; the person's own words and topics shared by both
    # speakers are what the person most likely repeats next.
    conv = st.get("conv") or []
    if not conv:
        return []
    who = _person(st)
    score, speakers, first = {}, {}, {}
    n = len(conv)
    for i, (spk, msg) in enumerate(conv):
        w8 = recency ** (n - 1 - i)
        if spk == who:
            w8 *= person_weight
        if i == n - 1:
            w8 *= last_bonus
        for w in _words(msg):
            score[w] = score.get(w, 0.0) + w8
            speakers.setdefault(w, set()).add(spk)
            first.setdefault(w, i)
    for w in score:
        if len(speakers[w]) > 1:
            score[w] *= 1.5
    return sorted(score, key=lambda w: (-score[w], first[w], w))


# mention_topic: standard-length reply steered to the person's live topic words (current message first, then
# words both speakers share), since the next message overlaps most with what the person is talking about now.
def mention_topic(st):
    r = _rank(st)
    return ("mention",) + tuple(r[:5]) if r else None


# holo_topic: compact-state reply. Replaces the full history with a compact state (fewer input tokens) while
# keeping the 6 highest-ranked topic words, so coverage is kept and tokens fall as the conversation grows.
def holo_topic(st):
    r = _rank(st)
    return ("holo",) + tuple(r[:6]) if r else None


# holomin_topic: minimal compact state with the same 6 words; the cheapest reply. Used from the second reply
# on, when enough topic words exist to carry the state; at the first reply it defers.
def holomin_topic(st):
    r = _rank(st)
    if len(r) < 3:
        return None
    return ("holomin",) + tuple(r[:6])


# mention_person_now: focus only on the person's current message (strong recency), for turns where the person
# opens a new subject or asks a question the next message will build on.
def mention_person_now(st):
    r = _rank(st, person_weight=2.5, recency=0.5, last_bonus=3.0)
    return ("mention",) + tuple(r[:4]) if r else None


# route_length: route by history length. Short history -> full-history reply with topic words (context is
# cheap); long history -> compact state with topic words (same coverage, far fewer input tokens).
def route_length(st):
    conv = st.get("conv") or []
    r = _rank(st)
    if not r:
        return None
    total = sum(len(str(m).split()) for _, m in conv)
    if total <= 120:
        return ("mention",) + tuple(r[:5])
    return ("holo",) + tuple(r[:6])


MOVES = {
    "mention_topic": mention_topic,
    "holo_topic": holo_topic,
    "holomin_topic": holomin_topic,
    "mention_person_now": mention_person_now,
    "route_length": route_length,
}
