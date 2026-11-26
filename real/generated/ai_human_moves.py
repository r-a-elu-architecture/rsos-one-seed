"""RSOS operator moves for the AI-human conversation host (the model replies as agent_2).

Each move: pure function of the state dict `st`; returns ("mention", w1, w2, ...) or None (standard reply).
Only st["conv"][: st["pos"][st["t"]] + 1] is read (never the future).
"""
import re
from collections import Counter

STOP = set("""a about above after again against all also am an and any are aren as at be because been before being
below between both but by can cannot could couldn did didn do does doesn doing don down during each else even ever
every few for from further get gets getting got had hadn has hasn have haven having he her here hers herself him
himself his how i if in into is isn it its itself just know like let lot me more most much must my myself no nor not
now of off oh ok okay on once one only or other ought our ours ourselves out over own pretty quite really right same
say said see she should shouldn so some something such sure than that thats the their theirs them themselves then
there these they thing things think this those though through to too under until up us very want was wasn way we
well were weren what when where which while who whom why will with won would wouldn yeah yes yet you your yours
yourself yourselves hello hi hey thanks thank good great nice going get go gonna also lol hmm umm uh im ive youre
dont cant didnt doesnt isnt wasnt thats whats it's i'm i've don't can't didn't doesn't isn't wasn't that's what's
you're they're we're there's i'll you'll i'd you'd""".split())

K = 3  # words per mention


def _cur(st):
    return st["pos"][st["t"]]


def _hist(st):
    return st["conv"][: _cur(st) + 1]


def _words(text):
    return [w.strip("'") for w in re.findall(r"[a-z][a-z']+", text.lower()) if w.strip("'") not in STOP and len(w.strip("'")) >= 3]


def _msg(st):
    return st["conv"][_cur(st)][1]


def _top(words, k=K, exclude=()):
    out = []
    for w, _ in Counter(words).most_common():
        if w not in out and w not in exclude:
            out.append(w)
        if len(out) >= k:
            break
    return out


def _say(ws):
    ws = [w for w in dict.fromkeys(ws) if w]
    return ("mention",) + tuple(ws[:K]) if ws else None


def _by_speaker(st, who):
    return [w for s, m in _hist(st) if s == who for w in _words(m)]


# beam: the whole reply focused on the person's current message: its most repeated, then longest content words.
def beam(st):
    ws = _words(_msg(st))
    c = Counter(ws)
    return _say(sorted(dict.fromkeys(ws), key=lambda w: (-c[w], -len(w))))


# inherit (O trace): words the person has carried across turns (in the current message and in earlier ones).
def inherit(st):
    cur = set(_words(_msg(st)))
    past = [w for s, m in _hist(st)[:-1] if s == "agent_1" for w in _words(m)]
    return _say([w for w in _top(past, 20) if w in cur])


# compress: many into one: the most frequent content words of the whole conversation so far.
def compress(st):
    return _say(_top([w for _, m in _hist(st) for w in _words(m)]))


# fuse: the person's current focus joined with the conversation's dominant topic (one word from each, then more).
def fuse(st):
    a = beam(st)
    b = compress(st)
    if not a or not b:
        return None
    return _say([a[1], b[1]] + list(a[2:]) + list(b[2:]))


# pierce: go straight to the question: content words of the person's question sentence(s).
def pierce(st):
    qs = [s for s in re.split(r"(?<=[.!?])\s+", _msg(st)) if s.strip().endswith("?")]
    return _say(_top([w for q in qs for w in _words(q)])) if qs else None


TROUBLE = re.compile(r"\b(not|no|never|can't|cannot|don't|won't|problem|hard|sad|worried|worry|sorry|bad|tired|"
                     r"stress|stressed|sick|lost|miss|afraid|scared|difficult|wrong|hate|upset|angry)\b", re.I)


# heal: the person signals trouble (negation, worry, problem) -> mention the content of that sentence.
def heal(st):
    ss = [s for s in re.split(r"(?<=[.!?])\s+", _msg(st)) if TROUBLE.search(s)]
    return _say(_top([w for s in ss for w in _words(s)])) if ss else None


# carry: words the person raised now that the model has not addressed yet in its earlier replies (carried forward).
def carry(st):
    said = set(_by_speaker(st, "agent_2"))
    return _say(_top(_words(_msg(st)), exclude=said))


# re-host: the model's own earlier words that the person took up in the current message (re-hosted on their side).
def re_host(st):
    mine = set(_by_speaker(st, "agent_2"))
    return _say([w for w in _top(_words(_msg(st)), 20) if w in mine])


# overlay: the current message overlaid on the person's whole history: current words weighted by past use.
def overlay(st):
    past = Counter(_by_speaker(st, "agent_1"))
    cur = list(dict.fromkeys(_words(_msg(st))))
    return _say(sorted(cur, key=lambda w: (-past[w], -len(w))))


# zoom (out): the conversation's opening topic, as the person set it in their first message.
def zoom(st):
    first = next((m for s, m in _hist(st) if s == "agent_1"), None)
    return _say(_top(_words(first))) if first and _hist(st)[-1][1] != first else None


# enter: one level inside the message: the last sentence (where the person hands the turn over).
def enter(st):
    ss = [s for s in re.split(r"(?<=[.!?])\s+", _msg(st).strip()) if _words(s)]
    return _say(_top(_words(ss[-1]))) if len(ss) > 1 else None


# contain: only one word: the strongest word of the current message (minimal steering, nothing else touched).
def contain(st):
    b = beam(st)
    return b[:2] if b else None


# route by state (colour): question -> pierce; trouble -> heal; short message -> compress (history); else beam.
def route(st):
    if len(_words(_msg(st))) < 3:
        return compress(st)
    return pierce(st) or heal(st) or beam(st)


MOVES = {
    "beam": beam,
    "inherit": inherit,
    "compress": compress,
    "fuse": fuse,
    "pierce": pierce,
    "heal": heal,
    "carry": carry,
    "re-host": re_host,
    "overlay": overlay,
    "zoom": zoom,
    "enter": enter,
    "contain": contain,
    "route": route,
}
