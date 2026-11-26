"""Composed RSOS moves for an AI replying to a person in a real conversation (domain 2).

Grammar: composition; the sequence of operators is the program, in VAKOG order
(see -> choose -> act -> trace -> result), with perspectives (inside = the person's own
words, across = the shared ground of both speakers, past = the whole conversation's trace).
Each move returns ONE native action: ("mention", w1, w2, ...) or None.
"""

import re

STOP = set("""
a about above after again against all almost also although always am among an and any anyone anything
are aren around as at back be because been before being below between both but by can cannot could
couldn did didn do does doesn doing don done down during each either else enough even ever every
everyone everything few for from further get gets getting go goes going gone got gotten had hadn has
hasn have haven having he her here hers herself him himself his how however i if in into is isn it its
itself just keep know let like likely lot lots made make many may maybe me might mine more most much
must my myself need never no nor not nothing now of off often oh ok okay on once one only or other
others our ours ourselves out over own pretty quite rather really right said same say says see seem
seems shall she should shouldn since so some someone something sometimes still such sure take than
thank thanks that the their theirs them themselves then there these they thing things think this those
though through to too toward under until up upon us use used very want wanted wants was wasn way we
well went were weren what whatever when where whether which while who whom whose why will with
without won would wouldn yeah yes yet you your yours yourself yourselves ll ve re im ive id youre
dont cant wont didnt doesnt isnt thats whats its hey hi hello good great nice fine sounds sound
lol haha wow cool also anyway actually definitely probably kind sort bit
""".split())

WORD = re.compile(r"[a-z][a-z']+")


# ---------------------------------------------------------------- operators
def words(msg):
    """V: the content words of one message, in order (lowercase, stopwords dropped)."""
    out = []
    for w in WORD.findall(str(msg).lower()):
        w = w.strip("'")
        if w.endswith("'s"):
            w = w[:-2]
        w = w.replace("'", "")
        if len(w) >= 3 and w not in STOP:
            out.append(w)
    return out


def see(st):
    """V: the conversation as turns; the person = the speaker of the current (last) message."""
    conv = [(str(s), str(m)) for s, m in (st.get("conv") or [])]
    person = conv[-1][0] if conv else None
    return {"conv": conv, "person": person}


def present(v):
    """Inside, now: the person's current message."""
    v["now"] = words(v["conv"][-1][1]) if v["conv"] else []
    return v


def past(v):
    """O trace: every word of the conversation so far, with in how many messages it appears
    and when it was last seen (recency index)."""
    df, last = {}, {}
    for i, (_, m) in enumerate(v["conv"]):
        for w in set(words(m)):
            df[w] = df.get(w, 0) + 1
            last[w] = i
    v["df"], v["last"] = df, last
    return v


def inside(v):
    """The person's own vocabulary across time, recency-weighted (the latest weighs most)."""
    n = len(v["conv"])
    score = {}
    for i, (s, m) in enumerate(v["conv"]):
        if s != v["person"]:
            continue
        for w in set(words(m)):
            score[w] = score.get(w, 0.0) + 1.0 / (n - i)
    v["own"] = score
    return v


def across(v):
    """Shared ground: words used by both speakers."""
    mine, theirs = set(), set()
    for s, m in v["conv"]:
        (mine if s == v["person"] else theirs).update(words(m))
    v["shared"] = mine & theirs
    return v


def choose(ranked, k):
    """A: select the protocol: the first k distinct words of a ranking."""
    out = []
    for w in ranked:
        if w not in out:
            out.append(w)
        if len(out) >= k:
            break
    return out


def act(ws):
    """K: land the selection as a native mention, only if there is something to land."""
    return ("mention",) + tuple(ws) if ws else None


# ---------------------------------------------------------------- moves
# see > present > choose > act: echo the person's current message: its first content words
# (most of the next message continues the current topic).
def m_echo(st):
    v = present(see(st))
    return act(choose(v["now"], 4))


# see > past > compress > choose > act: compress the whole conversation into its recurring
# core (words in two or more messages, latest first); these carry the topic forward.
def m_core(st):
    v = past(see(st))
    rec = [w for w in v["df"] if v["df"][w] >= 2]
    rec.sort(key=lambda w: (-v["df"][w], -v["last"][w]))
    return act(choose(rec, 4))


# see > inside > beam > choose > act: from inside the person, across time: the person's own
# words, recency-weighted, beamed into the reply (people reuse their own vocabulary).
def m_own(st):
    v = inside(see(st))
    ranked = sorted(v["own"], key=lambda w: -v["own"][w])
    return act(choose(ranked, 4))


# see > present > across > fuse > choose > act: fuse the person's current words with the
# shared ground of both speakers: current words that both have used come first, then the
# rest of the current message.
def m_fuse(st):
    v = across(present(see(st)))
    if not v["shared"]:
        return None
    ranked = [w for w in v["now"] if w in v["shared"]]
    ranked += sorted(w for w in v["shared"] if w not in ranked)
    return act(choose(ranked, 3))


# see > present > past > contain > choose > act: a small, contained landing: the two most
# salient current words (rare in the conversation so far, longest first), so the reply is
# steered only where the person is new.
def m_focus(st):
    v = past(present(see(st)))
    ranked = sorted(dict.fromkeys(v["now"]), key=lambda w: (v["df"].get(w, 0), -len(w)))
    return act(choose(ranked, 2))


MOVES = {
    "see>present>choose>act": m_echo,
    "see>past>compress>choose>act": m_core,
    "see>inside>beam>choose>act": m_own,
    "see>present>across>fuse>choose>act": m_fuse,
    "see>present>past>contain>choose>act": m_focus,
}
