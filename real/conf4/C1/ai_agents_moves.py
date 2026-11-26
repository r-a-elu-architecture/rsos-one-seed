# Domain 1: AI agents on tool-use tasks. Programs are pure functions of st.

CALL_BUDGET = 12
TOK_BUDGET = 16000


def _answers(st):
    return [b["answer"] for b in st.get("br", []) if b.get("answer") is not None]


def _majority(ans):
    best, n = None, 0
    for a in ans:
        c = ans.count(a)
        if c > n:
            best, n = a, c
    return best, n


def _unanswered(st):
    return [b for b in st.get("br", []) if b.get("answer") is None]


def _fresh_task(st):
    br = st.get("br", [])
    return st.get("calls", 0) == 0 and len(br) == 1 and br[0].get("calls", 0) == 0 and br[0].get("answer") is None


def _budget_left(st, calls=1, tok=1500):
    return st.get("calls", 0) + calls <= CALL_BUDGET and st.get("tok", 0) + tok <= TOK_BUDGET


# reuse_plan: at the very start of a task, run a stored plan of the same task shape at zero model calls
# (cheapest possible path to a correct answer); once any answer exists, commit immediately.
def reuse_plan(st):
    if _fresh_task(st):
        return ("reuse", st["br"][0]["id"])
    if _answers(st):
        return ("commit",)
    return None


# blind_plan: one model call writes the whole tool plan and a deterministic runtime computes every value
# (removes arithmetic/transcription errors and per-step token cost); commit as soon as an answer exists;
# if the plan produced no answer, continue the cheapest unanswered branch with ReAct steps.
def blind_plan(st):
    if _fresh_task(st):
        return ("blind", st["br"][0]["id"])
    if _answers(st):
        return ("commit",)
    un = _unanswered(st)
    if un and _budget_left(st):
        b = min(un, key=lambda x: (x.get("errors", 0), x.get("calls", 0)))
        return ("step", b["id"])
    return None


# blind_verify: plan mode first, then one independent ReAct attempt as a check; commit when two answers
# agree, open a third attempt only on disagreement (decision-theoretic: pay for a check only while the
# answer is still uncertain), and commit the majority when the budget runs low.
def blind_verify(st):
    if _fresh_task(st):
        return ("blind", st["br"][0]["id"])
    ans = _answers(st)
    _, n = _majority(ans) if ans else (None, 0)
    if n >= 2:
        return ("commit",)
    if ans and not _budget_left(st, 2, 3000):
        return ("commit",)
    un = _unanswered(st)
    if un:
        b = min(un, key=lambda x: x.get("calls", 0))
        if b.get("errors", 0) >= 3 and b.get("restarts", 0) == 0:
            return ("restart", b["id"])
        if ans and b.get("calls", 0) >= 4 and b.get("errors", 0) >= 2:
            return ("cross", b["id"], next(x["id"] for x in st["br"] if x.get("answer") is not None))
        return ("step", b["id"])
    if len(st.get("br", [])) < 3 and _budget_left(st, 3, 4000):
        return ("new",)
    if ans:
        return ("commit",)
    return None


# adaptive_sc: self-consistency with early stopping: greedy branch first, a second sample only to confirm,
# a third only on disagreement; restart branches stuck in repeated errors; commit at 2-vote agreement or
# when the remaining budget cannot buy another full attempt.
def adaptive_sc(st):
    br = st.get("br", [])
    ans = _answers(st)
    _, n = _majority(ans) if ans else (None, 0)
    if n >= 2:
        return ("commit",)
    if ans and not _budget_left(st, 2, 3000):
        return ("commit",)
    un = _unanswered(st)
    if un:
        b = min(un, key=lambda x: x.get("calls", 0))
        if b.get("errors", 0) >= 2 and b.get("restarts", 0) == 0 and b.get("calls", 0) >= 3:
            return ("restart", b["id"])
        return ("step", b["id"])
    if len(br) < 3 and _budget_left(st, 3, 4000):
        return ("new",)
    if ans:
        return ("commit",)
    return None


# budget_guard: protects accuracy-per-token: if an answer exists and remaining budget is thin, commit now;
# if no answer and the only live branch is failing, switch to plan mode on a fresh slot (one call that
# can still answer within budget) instead of spending further ReAct steps.
def budget_guard(st):
    ans = _answers(st)
    if ans and (st.get("calls", 0) >= 8 or st.get("tok", 0) >= 12000):
        return ("commit",)
    if not ans:
        un = _unanswered(st)
        if un:
            b = max(un, key=lambda x: x.get("errors", 0))
            if b.get("errors", 0) >= 2 and _budget_left(st, 1, 2500):
                return ("blind", b["id"])
    return None


MOVES = {
    "reuse_plan": reuse_plan,
    "blind_plan": blind_plan,
    "blind_verify": blind_verify,
    "adaptive_sc": adaptive_sc,
    "budget_guard": budget_guard,
}
