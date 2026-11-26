# Domain 2: replying to a person (C3). Value = overlap with the person's NEXT message, then fewer tokens.
# Idea: the person's next message reuses their own recent content words and the live topic words;
# steer the reply to mention exactly those (lexical entrainment), and use compact state when history is long.
import re

_STOP = set("""
a about above after again against all also am an and any are aren as at be because been before being below
between both but by can cannot could couldn did didn do does doesn doing don down during each else even ever
every few for from further get gets getting got had hadn has hasn have haven having he her here hers herself him
himself his how however i if in into is isn it its itself just know let like ll me might more most much must
my myself no nor not now of off on once one only or other ought our ours ourselves out over own really re same
say said see seem she should shouldn so some such sure than that thats the their theirs them themselves then
there these they thing things think this those though through to too under until up upon us very was wasn way we
well were weren what when where which while who whom why will with won would wouldn yes yeah yet you your yours
yourself yourselves oh okay ok hi hello hey thanks thank lot lol haha gonna wanna kind sort maybe actually pretty
going go want make made something anything nothing everything someone anyone im ive dont didnt doesnt cant wont
isnt youre theyre thats whats its id ill youve weve s t d m ve also still back good great nice cool right much
many time times day today tomorrow yesterday tell told feel feels felt quite lot lots mostly usually probably
definitely totally pretty kinda guess mean means
""".split())


def _words(text):
    out = []
    for w in re.findall(r"[a-z][a-z']*", str(text).lower()):
        w = w.replace("'", "")
        if len(w) >= 3 and w not in _STOP:
            out.append(w)
    return out


def _person(st):
    conv = st["conv"]
    return conv[-1][0] if conv else None


def _score(st, own_w=1.0, other_w=0.5, decay=0.75, last_bonus=1.5):
    conv = st["conv"]
    if not conv:
        return {}
    me = _person(st)
    sc = {}
    n = len(conv)
    for i, (spk, msg) in enumerate(conv):
        age = n - 1 - i
        w = (decay ** age) * (own_w if spk == me else other_w)
        if age == 0:
            w *= last_bonus
        seen = set()
        for x in _words(msg):
            # first occurrence per message counts fully, repeats a little
            sc[x] = sc.get(x, 0.0) + (w if x not in seen else 0.3 * w)
            seen.add(x)
    return sc


def _top(sc, k):
    return [w for w, _ in sorted(sc.items(), key=lambda kv: (-kv[1], kv[0]))[:k]]


def _shared_boost(st, sc):
    # words used by BOTH speakers are the conversation's live topic: boost them
    me = _person(st)
    mine, theirs = set(), set()
    for spk, msg in st["conv"]:
        (mine if spk == me else theirs).update(_words(msg))
    out = dict(sc)
    for w in mine & theirs:
        out[w] = out.get(w, 0.0) * 1.6
    return out


# mention_recent: mention the 4 strongest content words, weighted toward the person's own recent words
# (they tend to repeat them next), keeping the full history so the reply stays natural.
def mention_recent(st):
    ws = _top(_score(st), 4)
    return ("mention",) + tuple(ws) if ws else None


# mention_topic: mention the 5 live topic words (shared by both speakers, recency-weighted) to keep the
# reply on the thread the person will continue.
def mention_topic(st):
    ws = _top(_shared_boost(st, _score(st, other_w=0.7, decay=0.85)), 5)
    return ("mention",) + tuple(ws) if ws else None


# holo_topic: compact whole-state reply with the 6 best words; cuts input tokens on long histories while
# the explicit words preserve coverage.
def holo_topic(st):
    ws = _top(_shared_boost(st, _score(st, decay=0.85)), 6)
    return ("holo",) + tuple(ws) if ws else None


# holomin_recent: minimal compact state + 6 recency-weighted words; cheapest input, for when the last
# messages carry what the person will say next.
def holomin_recent(st):
    ws = _top(_score(st), 6)
    return ("holomin",) + tuple(ws) if ws else None


# routed: early in a conversation (little history) mention the person's words with full context; once the
# history is long, switch to compact state (same coverage words, far fewer input tokens).
def routed(st):
    conv = st["conv"]
    total = sum(len(str(m).split()) for _, m in conv)
    sc = _shared_boost(st, _score(st, decay=0.8))
    if len(conv) <= 3 or total < 120:
        ws = _top(sc, 4)
        return ("mention",) + tuple(ws) if ws else None
    ws = _top(sc, 6)
    return ("holo",) + tuple(ws) if ws else None


MOVES = {
    "mention_recent": mention_recent,
    "mention_topic": mention_topic,
    "holo_topic": holo_topic,
    "holomin_recent": holomin_recent,
    "routed": routed,
}
