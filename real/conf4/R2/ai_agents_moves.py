# RSOS R2 programs, domain 1: AI agents solving tool-use tasks.
# Host = computer: every program runs V -> A -> K -> O -> G (U157):
#   V (see)     read the branches: answers, majority, errors, budget left
#   A (choose)  the heard signal selects the room (route by state, U5/U64/U69)
#   K (act)     the room's operator chain, in order, returns one action
#   O (trace)   the branches' errors/restarts are the trace carried forward (U143)
#   G (result)  the committed majority answer
# Pure functions of `st`; standard library only.

from collections import Counter

CALLS_MAX = 12
TOK_MAX = 16000


# ---------------------------------------------------------------- V: see
def _see(st):
    br = st.get("br") or []
    answers = [b.get("answer") for b in br if b.get("answer") is not None]
    cnt = Counter(answers)
    top, top_n = (cnt.most_common(1)[0] if cnt else (None, 0))
    unanswered = [b for b in br if b.get("answer") is None]
    return {
        "br": br,
        "answers": answers,
        "cnt": cnt,
        "top": top,
        "top_n": top_n,
        "unanswered": unanswered,
        "calls_left": CALLS_MAX - int(st.get("calls", 0)),
        "tok_left": TOK_MAX - int(st.get("tok", 0)),
        "calls": int(st.get("calls", 0)),
    }


# ---------------------------------------------------------------- A: choose the room
def _room(v):
    if v["calls_left"] <= 1 or v["tok_left"] < 2500:
        return "overload"
    if v["top_n"] >= 2:
        return "stable"
    if len(v["cnt"]) >= 2:
        return "uncertainty"
    if v["top_n"] == 1:
        # one answer: stable if its branch read no error, else uncertainty
        b = next(b for b in v["br"] if b.get("answer") is not None)
        return "stable" if int(b.get("errors", 0)) == 0 and not v["unanswered"] else "uncertainty"
    return "deficit"  # no answer yet


def _best_unanswered(v):
    # Tiger (U104): the closest, most precise path = the unanswered branch with fewest errors
    if not v["unanswered"]:
        return None
    return min(v["unanswered"], key=lambda b: (int(b.get("errors", 0)), -int(b.get("calls", 0))))


def _new_slot(v):
    return len(v["br"]) if len(v["br"]) < 3 else None


# ---------------------------------------------------------------- Program 1
# house_blind_vote
# Rooms (trigger -> chain):
#   overload    (<=1 call or <2500 tokens left)   -> commit if any answer, else Tiger step   [Law 6, Law 4]
#   stable      (majority >= 2, or one clean answer) -> commit (withholding further calls)     [Law 4]
#   uncertainty (answers disagree / answer read errors) -> P8 triggered vote: a second future in
#               plan mode on a fresh slot (blind), commit when no slot is left              [P8, Law 2]
#   deficit     (no answer) -> calls==0: blind(0) (keys only, runtime computes values);
#               else a fresh blind slot (P9 complementation of the ReAct branch), else Tiger step [Law 2, P9]
# Chain: V see -> A room -> K (blind | vote | commit) -> O errors carried -> G majority.
# Laws: Law 2 (blind operation), Law 4 (land only where it changes the task's future), Law 1 (read scope:
#   the plan names keys only), Law 6 (budget edge degrades gracefully to commit), Law 0 (never an invalid action:
#   every return is checked against the budget and the branch slots).
# Invariant + check: no call is spent once a majority exists (check: room stable -> commit, 0 calls);
#   no action leaves the 12-call / 16k-token budget (check: overload room commits or takes one step).
def house_blind_vote(st):
    v = _see(st)
    room = _room(v)
    if room == "overload":
        if v["answers"]:
            return ("commit",)
        b = _best_unanswered(v)
        return ("step", b["id"]) if b else ("commit",)
    if room == "stable":
        return ("commit",)
    if room == "uncertainty":
        s = _new_slot(v)
        if s is not None and v["calls_left"] >= 2:
            return ("blind", s)
        return ("commit",)
    # deficit: no answer
    if v["calls"] == 0 and v["br"]:
        return ("blind", v["br"][0]["id"])
    s = _new_slot(v)
    if s is not None:
        return ("blind", s)
    b = _best_unanswered(v)
    return ("step", b["id"]) if b else None


# ---------------------------------------------------------------- Program 2
# house_reuse_blind
# Rooms: as house_blind_vote, with the deficit room opened by the KEY first:
#   deficit, calls==0 -> reuse(0): a stored plan of the same task shape at zero model calls
#               (Law 5: send nothing the receiver can derive; inherit the trace, U152/INHERIT);
#               when no plan exists the host falls back to the standard step, and the next decision
#               routes to the blind slot (P9).
# Chain: V -> A -> K (reuse -> blind -> vote -> commit) -> O -> G.
# Laws: Law 5 (relations raise the limit: the stored plan), Law 2, Law 4, Law 6, Law 0.
# Invariant + check: at most one reuse attempt per task (check: reuse only at calls==0 on slot 0).
def house_reuse_blind(st):
    v = _see(st)
    if v["calls"] == 0 and not v["answers"] and v["br"] and int(v["br"][0].get("calls", 0)) == 0:
        return ("reuse", v["br"][0]["id"])
    return house_blind_vote(st)


# ---------------------------------------------------------------- Program 3
# house_react_heal
# Rooms (no plan mode; the ReAct host healed in place):
#   overload    -> commit if any answer, else Tiger step                              [Law 6]
#   stable      -> commit                                                             [Law 4]
#   deficit     -> a branch with >=2 errors and no restart: restart it (White Dragon U90 / P3:
#                  repair only the part that differs); else Tiger step on the cleanest branch  [Law 3, P3]
#   uncertainty -> P8 triggered vote: new attempt at 0.7 when a slot is free, else commit  [P8]
# Chain: V -> A -> K (heal | step | new | commit) -> O (errors, restarts) -> G.
# Laws: Law 3 (living structure), Law 4, Law 6, Law 0 (restart only where restarts==0).
# Invariant + check: a branch is restarted at most once (check: restarts==0 before restart).
def house_react_heal(st):
    v = _see(st)
    room = _room(v)
    if room == "overload":
        if v["answers"]:
            return ("commit",)
        b = _best_unanswered(v)
        return ("step", b["id"]) if b else ("commit",)
    if room == "stable":
        return ("commit",)
    if room == "uncertainty":
        if len(v["br"]) < 3 and v["calls_left"] >= 3:
            return ("new",)
        if v["unanswered"]:
            return ("step", _best_unanswered(v)["id"])
        return ("commit",)
    # deficit
    sick = [b for b in v["unanswered"] if int(b.get("errors", 0)) >= 2 and int(b.get("restarts", 0)) == 0]
    if sick and v["calls_left"] >= 4:
        return ("restart", sick[0]["id"])
    b = _best_unanswered(v)
    return ("step", b["id"]) if b else None


# ---------------------------------------------------------------- Program 4
# cross_golden
# Rooms:
#   uncertainty with an unanswered branch -> golden light (U101: best path by shared relations):
#               cross(b, src): the unanswered branch with fewest errors is told the answer of the
#               answered branch with fewest errors (Law 5: send only what it cannot derive)
#   every other room -> house_blind_vote
# Chain: V -> A -> K (cross | blind | vote | commit) -> O -> G.
# Laws: Law 5, Law 2, Law 4, Law 0.
# Invariant + check: cross only targets an unanswered branch and a different answered source.
def cross_golden(st):
    v = _see(st)
    room = _room(v)
    if room == "uncertainty" and v["unanswered"] and v["answers"] and v["calls_left"] >= 2:
        b = _best_unanswered(v)
        srcs = [x for x in v["br"] if x.get("answer") is not None and x["id"] != b["id"]]
        if srcs:
            src = min(srcs, key=lambda x: int(x.get("errors", 0)))
            return ("cross", b["id"], src["id"])
    return house_blind_vote(st)


# ---------------------------------------------------------------- Program 5
# landing_commit
# Rooms:
#   stable (an answer exists, none conflicting) -> commit: withhold every further call  [Law 4]
#   any other state -> None (does not apply; the standard runs)
# Chain: V -> A -> K commit -> G.
# Laws: Law 4 (withholding is a move), Law 0 (no action where it is not needed).
# Invariant + check: commits only with >=1 answer and exactly one distinct answer.
def landing_commit(st):
    v = _see(st)
    if v["answers"] and len(v["cnt"]) == 1:
        return ("commit",)
    return None


MOVES = {
    "house_blind_vote": house_blind_vote,
    "house_reuse_blind": house_reuse_blind,
    "house_react_heal": house_react_heal,
    "cross_golden": cross_golden,
    "landing_commit": landing_commit,
}
