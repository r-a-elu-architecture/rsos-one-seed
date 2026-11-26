# Domain 1: AI agents solving tool-use tasks. Each program is a pure function of `st`.


def _answers(st):
    return [b["answer"] for b in st.get("br", []) if b.get("answer") is not None]


def _majority(st):
    ans = _answers(st)
    if not ans:
        return None, 0
    counts = {}
    for a in ans:
        counts[a] = counts.get(a, 0) + 1
    best = max(counts.items(), key=lambda kv: kv[1])
    return best[0], best[1]


def _open_branch(st):
    for b in st.get("br", []):
        if b.get("answer") is None:
            return b
    return None


def _free_slot(st):
    n = len(st.get("br", []))
    return n if n < 3 else None


# reuse_plan: at the very start of a task, run a stored plan of the same task shape at zero model calls
# (cheapest possible correct path when a plan exists); once any answer exists, commit immediately.
def reuse_plan(st):
    if st.get("calls", 0) == 0 and not _answers(st):
        return ("reuse", 0)
    if _answers(st):
        return ("commit",)
    return None


# blind_plan: plan mode. One model call writes the whole tool plan and a deterministic runtime computes every
# value, which removes arithmetic and transcription errors and the per-step token cost of ReAct.
# Start of task -> blind on slot 0; a stalled ReAct branch with no answer -> blind on a free slot; answer -> commit.
def blind_plan(st):
    if _answers(st):
        return ("commit",)
    if st.get("calls", 0) == 0:
        return ("blind", 0)
    slot = _free_slot(st)
    if slot is not None and st.get("calls", 0) <= 10:
        return ("blind", slot)
    b = _open_branch(st)
    return ("step", b["id"]) if b else None


# plan_then_verify: cheap independent verification (accuracy first, tokens second). First answer comes from a
# plan; a second independent attempt checks it; agreement of two -> commit; disagreement -> a third tie-breaker
# that is told the other answer (cross), then commit the majority.
def plan_then_verify(st):
    calls, tok = st.get("calls", 0), st.get("tok", 0)
    ans = _answers(st)
    maj, cnt = _majority(st)
    if not ans:
        if calls == 0:
            return ("blind", 0)
        b = _open_branch(st)
        return ("step", b["id"]) if b else ("commit",)
    if cnt >= 2 or calls >= 11 or tok >= 14500:
        return ("commit",)
    b = _open_branch(st)
    if b is not None:
        src = next(x["id"] for x in st["br"] if x.get("answer") is not None)
        if len(set(ans)) > 1:
            return ("cross", b["id"], src)
        return ("step", b["id"])
    slot = _free_slot(st)
    if slot is not None:
        return ("new",)
    return ("commit",)


# react_repair: ReAct on branch 0 with error-driven repair. Two or more tool errors on a branch signal a bad
# trajectory, so restart it once at temperature 0.7 instead of spending the budget on it; commit as soon as
# an answer exists or the budget is nearly exhausted.
def react_repair(st):
    if _answers(st):
        return ("commit",)
    calls, tok = st.get("calls", 0), st.get("tok", 0)
    b = _open_branch(st)
    if b is None:
        return ("commit",)
    if len(b.get("errors", [])) >= 2 and b.get("restarts", 0) == 0 and calls <= 8 and tok <= 11000:
        return ("restart", b["id"])
    return ("step", b["id"])


# budget_commit: stop spending once the answer is settled. Commit as soon as a majority of 2 exists, or any
# answer exists and the remaining budget is too small for an independent check; otherwise defer (None).
def budget_commit(st):
    maj, cnt = _majority(st)
    if maj is None:
        return None
    if cnt >= 2:
        return ("commit",)
    if st.get("calls", 0) >= 9 or st.get("tok", 0) >= 12000:
        return ("commit",)
    if len(st.get("br", [])) == 1:
        return ("commit",)
    return None


MOVES = {
    "reuse_plan": reuse_plan,
    "blind_plan": blind_plan,
    "plan_then_verify": plan_then_verify,
    "react_repair": react_repair,
    "budget_commit": budget_commit,
}
