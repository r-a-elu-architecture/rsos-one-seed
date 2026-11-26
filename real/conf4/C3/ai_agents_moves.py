# Domain 1: tool-use agent decision programs (C3).
# Pure functions of st; standard library only.

CALL_BUDGET = 12
TOK_BUDGET = 16000


def _answers(st):
    return [b["answer"] for b in st["br"] if b.get("answer") is not None]


def _majority(st):
    ans = _answers(st)
    if not ans:
        return None, 0
    counts = {}
    for a in ans:
        k = str(a).strip().lower()
        counts[k] = counts.get(k, 0) + 1
    best = max(counts.values())
    return best, len(ans)


def _open(st):
    return [b for b in st["br"] if b.get("answer") is None]


def _fresh_slot(st):
    # an untouched unanswered branch, else a new slot id, else None
    for b in st["br"]:
        if b.get("answer") is None and b.get("calls", 0) == 0:
            return b["id"]
    if len(st["br"]) < 3:
        ids = [b["id"] for b in st["br"]]
        return max(ids) + 1 if ids else 0
    return None


def _budget_left(st):
    return CALL_BUDGET - st["calls"], TOK_BUDGET - st["tok"]


def _react_continue(st):
    # best ReAct continuation: restart error-stuck branches, otherwise step the healthiest open branch
    opn = _open(st)
    if not opn:
        return ("commit",)
    calls_left, tok_left = _budget_left(st)
    if calls_left <= 1 or tok_left < 1500:
        return ("commit",) if _answers(st) else ("step", min(opn, key=lambda b: b["errors"])["id"])
    for b in opn:
        if b["errors"] >= 2 and b["restarts"] == 0 and calls_left >= 4:
            return ("restart", b["id"])
    b = min(opn, key=lambda x: (x["errors"], -x["calls"]))
    return ("step", b["id"])


# reuse: at task start run a stored plan of the same task shape at zero model calls; once any answer
# exists commit it. Zero-cost when a plan exists, and identical to the standard when it does not.
def reuse_first(st):
    if not _answers(st):
        if st["calls"] == 0:
            return ("reuse", st["br"][0]["id"] if st["br"] else 0)
        return None
    return ("commit",)


# blind: one model call writes the whole tool plan; the deterministic runtime computes all values
# (no arithmetic/transcription errors, no ReAct loop). Commit as soon as it answers.
def blind_first(st):
    if not _answers(st):
        if st["calls"] == 0:
            s = _fresh_slot(st)
            return ("blind", s if s is not None else 0)
        return None
    return ("commit",)


# reuse -> blind -> verified commit: try the free stored plan, then a one-call blind plan on a second slot;
# commit when two answers agree; on disagreement add a third independent (blind) attempt as tie-breaker
# while budget allows, then commit the majority. Accuracy first at near-minimal tokens.
def plan_verify(st):
    best, n = _majority(st)
    calls_left, tok_left = _budget_left(st)
    if n == 0:
        if st["calls"] == 0 and all(b.get("calls", 0) == 0 for b in st["br"]) and \
                all(b.get("restarts", 0) == 0 for b in st["br"]) and len(st["br"]) == 1:
            return ("reuse", st["br"][0]["id"])
        s = _fresh_slot(st)
        if s is not None and calls_left >= 1 and tok_left > 1500:
            return ("blind", s)
        return _react_continue(st)
    if best >= 2:
        return ("commit",)
    if calls_left < 1 or tok_left < 1500:
        return ("commit",)
    s = _fresh_slot(st)
    if s is not None:
        return ("blind", s)
    # all 3 slots used and no agreement: let an open branch arbitrate with the others' answer, else commit
    opn = _open(st)
    if opn and calls_left >= 2:
        src = next(b["id"] for b in st["br"] if b.get("answer") is not None)
        return ("cross", opn[0]["id"], src)
    return ("commit",)


# blind with a single cheap check: blind plan first; if it fails to answer (bad plan) fall back to a
# fresh blind on another slot, then to robust ReAct; commit the first answer (no second opinion).
def blind_retry(st):
    if _answers(st):
        return ("commit",)
    calls_left, tok_left = _budget_left(st)
    s = _fresh_slot(st)
    if s is not None and calls_left >= 1 and tok_left > 1500:
        return ("blind", s)
    return _react_continue(st)


# adaptive ReAct ensemble (no plan mode): step the healthiest branch, restart error-stuck branches,
# open a second attempt to verify a first answer when budget is ample, cross-inform on disagreement,
# and commit as soon as two answers agree or the budget runs short.
def adaptive_react(st):
    best, n = _majority(st)
    calls_left, tok_left = _budget_left(st)
    if n and best >= 2:
        return ("commit",)
    if n and (calls_left <= 2 or tok_left < 3000):
        return ("commit",)
    opn = _open(st)
    if n == 1 and not opn:
        if len(st["br"]) < 3 and calls_left >= 4 and tok_left > 6000:
            return ("new",)
        return ("commit",)
    if n >= 2 and best < 2:
        if opn:
            src = next(b["id"] for b in st["br"] if b.get("answer") is not None)
            return ("cross", opn[0]["id"], src)
        if len(st["br"]) < 3 and calls_left >= 3:
            return ("new",)
        return ("commit",)
    return _react_continue(st)


MOVES = {
    "reuse_first": reuse_first,
    "blind_first": blind_first,
    "plan_verify": plan_verify,
    "blind_retry": blind_retry,
    "adaptive_react": adaptive_react,
}
