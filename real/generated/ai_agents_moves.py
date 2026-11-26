"""RSOS operator moves for the AI-agent tool-use host (one decision = next action on the current task).

Each move: pure function of the state dict `st`; returns one native action tuple or None.
Native actions: ("step", b) · ("new",) · ("restart", b) · ("cross", b, src) · ("commit",).
"""
from collections import Counter

CALLS_MAX, TOK_MAX, BR_MAX = 12, 16000, 3


def _open(st):
    return [b for b in st["br"] if b["answer"] is None]


def _done(st):
    return [b for b in st["br"] if b["answer"] is not None]


def _majority(st):
    c = Counter(b["answer"] for b in _done(st))
    return c.most_common(1)[0] if c else (None, 0)


def _per_call(st):
    return st["tok"] / max(1, st["calls"]) if st["calls"] else 1500.0


def _room(st, calls=1):
    return (CALLS_MAX - st["calls"]) >= calls and (TOK_MAX - st["tok"]) >= calls * _per_call(st)


# heal (P3 part check and repair): repair only the failing branch: restart the unanswered branch with the most errors.
def heal(st):
    bad = [b for b in _open(st) if b["errors"] >= 2 and b["restarts"] == 0]
    if not bad or not _room(st, 2):
        return None
    return ("restart", max(bad, key=lambda b: b["errors"])["id"])


# beam: the whole step's call goes to the healthiest unanswered branch (fewest errors, then fewest tokens).
def beam(st):
    op = _open(st)
    if not op or not _room(st):
        return None
    return ("step", min(op, key=lambda b: (b["errors"], b["tok"]))["id"])


# contain: isolate a failing branch (errors >= 2) and spend the step on a healthy unanswered one.
def contain(st):
    op = _open(st)
    bad = [b for b in op if b["errors"] >= 2]
    good = [b for b in op if b["errors"] < 2]
    if not bad or not good or not _room(st):
        return None
    return ("step", min(good, key=lambda b: (b["errors"], -b["calls"]))["id"])


# compress: many answers into one: once a strict majority exists (>= 2 agree), commit it and stop spending.
def compress(st):
    ans, n = _majority(st)
    return ("commit",) if ans is not None and n >= 2 else None


# vote (P8 triggered): only one answer and its branch read uncertainty (errors) -> open one more future.
def vote(st):
    d = _done(st)
    if len(d) != 1 or _open(st) or len(st["br"]) >= BR_MAX or not _room(st, 3):
        return None
    return ("new",) if d[0]["errors"] > 0 else None


# pierce: answered branches disagree with no majority -> a fresh attempt pierces the tie.
def pierce(st):
    d = _done(st)
    ans, n = _majority(st)
    if len(d) < 2 or n >= 2 or _open(st) or len(st["br"]) >= BR_MAX or not _room(st, 3):
        return None
    return ("new",)


# fuse: join two branches: an erring unanswered branch takes its next step told the cleanest answer.
def fuse(st):
    d = _done(st)
    op = [b for b in _open(st) if b["errors"] > 0]
    if not d or not op or not _room(st):
        return None
    src = min(d, key=lambda b: b["errors"])
    return ("cross", max(op, key=lambda b: b["errors"])["id"], src["id"])


# inherit: a restarted (fresh-context) branch inherits the trace of the best answered branch.
def inherit(st):
    d = _done(st)
    op = [b for b in _open(st) if b["restarts"] == 1]
    if not d or not op or not _room(st):
        return None
    return ("cross", op[0]["id"], min(d, key=lambda b: b["errors"])["id"])


# carry: a clean single answer (no errors, no disagreement) is committed; the unused budget is carried (tokens saved).
def carry(st):
    d = _done(st)
    if not d or (_open(st) and len(d) < 2):
        return None
    clean = all(b["errors"] == 0 for b in d) and len(set(b["answer"] for b in d)) == 1
    return ("commit",) if clean else None


# membrane (Law 0): near the budget bound (calls or tokens) commit what exists instead of overrunning.
def membrane(st):
    if not _done(st):
        return None
    near = (CALLS_MAX - st["calls"]) <= 1 or (TOK_MAX - st["tok"]) < 1.5 * _per_call(st)
    return ("commit",) if near else None


# zoom (out): a branch that used over half the budget unanswered is long-context; zoom out to a fresh attempt.
def zoom(st):
    op = _open(st)
    long_ = [b for b in op if b["tok"] > TOK_MAX / 2 or b["calls"] >= CALLS_MAX / 2]
    if not long_ or len(st["br"]) >= BR_MAX or not _room(st, 3):
        return None
    return ("new",)


# enter: go deeper inside the branch closest to finishing (most calls already made, errors < 2).
def enter(st):
    op = [b for b in _open(st) if b["errors"] < 2]
    if not op or not _room(st):
        return None
    return ("step", max(op, key=lambda b: (b["calls"], -b["errors"]))["id"])


# re-host: the greedy branch (temp 0) that keeps erring is re-hosted at temperature 0.7 (restart).
def re_host(st):
    b = [b for b in _open(st) if b["temp"] == 0 and b["errors"] >= 1 and b["restarts"] == 0]
    return ("restart", b[0]["id"]) if b and _room(st, 2) else None


# overlay: answers disagree and an unanswered branch exists -> it steps with the majority/cleanest answer overlaid.
def overlay(st):
    d = _done(st)
    op = _open(st)
    if len(set(b["answer"] for b in d)) < 2 or not op or not _room(st):
        return None
    ans, n = _majority(st)
    src = [b for b in d if b["answer"] == ans] if n >= 2 else d
    return ("cross", op[0]["id"], min(src, key=lambda b: b["errors"])["id"])


# apoptosis: a restarted branch that still errs (>= 2) is dropped: commit if an answer exists, else a new attempt.
def apoptosis(st):
    dead = [b for b in _open(st) if b["restarts"] == 1 and b["errors"] >= 2]
    if not dead:
        return None
    if _done(st):
        return ("commit",)
    return ("new",) if len(st["br"]) < BR_MAX and _room(st, 2) else None


# route by state (colour): red = failing branch -> heal; green = agreed answer -> commit; else beam.
def route(st):
    return membrane(st) or compress(st) or heal(st) or carry(st) or beam(st)


MOVES = {
    "heal": heal,
    "beam": beam,
    "contain": contain,
    "compress": compress,
    "vote": vote,
    "pierce": pierce,
    "fuse": fuse,
    "inherit": inherit,
    "carry": carry,
    "membrane": membrane,
    "zoom": zoom,
    "enter": enter,
    "re-host": re_host,
    "overlay": overlay,
    "apoptosis": apoptosis,
    "route": route,
}
