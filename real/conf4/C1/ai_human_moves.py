# Domain 2: AI replying to a person. Programs pick content words the person is likely to use next.
import re

_STOP = set("""
a about above after again against all also am an and any are aren as at be because been before being below
between both but by can cannot could couldn did didn do does doesn doing don down during each few for from
further had hadn has hasn have haven having he her here hers herself him himself his how i if in into is isn it
its itself just let me more most mustn my myself no nor not now of off on once only or other ought our ours
ourselves out over own same shan she should shouldn so some such than that the their theirs them themselves
then there these they this those through to too under until up very was wasn we were weren what when where
which while who whom why will with won would wouldn you your yours yourself yourselves ll ve re im ive youre
dont didnt cant wont thats its isnt yeah yes yep yup okay ok oh ah uh um hmm haha hahaha lol well really
like just know think get got go going gonna wanna thing things lot lots much many way also maybe sure
good great nice cool fun right actually pretty kind sort something anything everything nothing one two
would could should might must say said tell told see make made want need still even back day time hey hi
hello thanks thank bye
""".split())


def _words(msg):
    out = []
    for w in re.findall(r"[a-z][a-z']*", str(msg).lower()):
        w = w.replace("'", "")
        if len(w) >= 3 and w not in _STOP:
            out.append(w)
    return out


def _person(st):
    conv = st.get("conv") or []
    return conv[-1][0] if conv else None


def _scores(st, decay=0.75, person_bonus=1.4):
    conv = st.get("conv") or []
    me = _person(st)
    n = len(conv)
    sc, seen_in = {}, {}
    for i, (spk, msg) in enumerate(conv):
        age = n - 1 - i
        wgt = (decay ** age) * (person_bonus if spk == me else 1.0)
        for w in set(_words(msg)):
            sc[w] = sc.get(w, 0.0) + wgt
            seen_in[w] = seen_in.get(w, 0) + 1
    for w in sc:
        if seen_in[w] >= 2:
            sc[w] *= 1.0 + 0.3 * (seen_in[w] - 1)
    return sc


def _top(st, k, **kw):
    sc = _scores(st, **kw)
    order = sorted(sc, key=lambda w: (-sc[w], w))
    return order[:k]


# mention_salient: ask the reply to mention the 4 most salient content words (recency-weighted, person's own
# words weighted up, recurring topic words boosted) - the words the person most likely repeats next.
def mention_salient(st):
    ws = _top(st, 4)
    return ("mention",) + tuple(ws) if ws else None


# mention_echo: the person's next turn usually continues their current message; mention up to 3 content words
# of that message plus the strongest recurring topic word of the conversation.
def mention_echo(st):
    conv = st.get("conv") or []
    if not conv:
        return None
    sc = _scores(st)
    last = []
    for w in _words(conv[-1][1]):
        if w not in last:
            last.append(w)
    last.sort(key=lambda w: -sc.get(w, 0))
    ws = last[:3]
    for w in _top(st, 6, decay=0.95):
        if w not in ws:
            ws.append(w)
            break
    return ("mention",) + tuple(ws) if ws else None


# holo_salient: compact whole-conversation state instead of the full history (fewer input tokens, topic kept)
# plus 6 salient words to cover; strongest when the history is long.
def holo_salient(st):
    ws = _top(st, 6)
    return ("holo",) + tuple(ws) if ws else None


# holomin_salient: minimal compact state (fewest input tokens) with the 6 salient words; the words carry the
# coverage, the minimal state carries the cost saving.
def holomin_salient(st):
    ws = _top(st, 6)
    return ("holomin",) + tuple(ws) if ws else None


# route_by_length: short histories -> full-history reply with 5 targeted words (history is cheap and context
# helps); long histories -> holo, where the compact state saves the most tokens.
def route_by_length(st):
    conv = st.get("conv") or []
    total = sum(len(str(m).split()) for _, m in conv)
    ws = _top(st, 6)
    if not ws:
        return None
    if total < 120:
        return ("mention",) + tuple(ws[:5])
    if total < 400:
        return ("holo",) + tuple(ws)
    return ("holomin",) + tuple(ws)


MOVES = {
    "mention_salient": mention_salient,
    "mention_echo": mention_echo,
    "holo_salient": holo_salient,
    "holomin_salient": holomin_salient,
    "route_by_length": route_by_length,
}
