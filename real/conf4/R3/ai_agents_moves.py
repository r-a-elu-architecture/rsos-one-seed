# RSOS R3 programs, domain 1: AI agents solving tool-use tasks.
# Host = computer: VAKOG order V -> A -> K -> O -> G (U157).
#   V (see)    : read the branches: answers, agreement, errors, budget (Law 1: only these fields are read).
#   A (choose) : the room is selected by the host's state (route by state U5 / U64 / U69):
#                overload  : calls >= 11 or tokens >= 13,500 (the budget's bound is near)
#                deficit   : no branch has answered yet (U103: the lack decides where to land)
#                stable    : one answer, or a strict majority >= 2, from a clean branch (no errors)
#                uncertainty: answers disagree, or the only answer came from a branch that met errors
# K (act)    : the room's composed operator chain, in order.
# O (trace)  : the branch ids carry the trace (slot 0 = the blind / reused plan slot), errors and restarts.
# G (result) : commit = the majority answer of the whole.
# Laws: Law 0 (each program checks itself: it never returns an action outside the allowed set; when its own room
# reading fails it returns None and the standard stays), Law 2 (blind: one call sends only keys; the deterministic
# runtime computes every value), Law 3 / P3 (White Dragon U90: restart only the branch that differs (errors), never
# the whole task), Law 4 (land only where it changes the task's future: commit as soon as the answer is stable;
# withholding further calls is a move), Law 5 (cross: tell a branch only what it cannot derive, the other answer),
# P8 triggered (a vote of futures only when the structure reads uncertainty), Law 6 (overload: graceful landing on
# the best answer at hand instead of running out of budget unanswered).

CALLS_MAX = 12
TOK_MAX = 16000


def _see(st):
    # V: the image of the task state (read scope: branches + budget only)
    br = list(st.get("br") or [])
    ans = [b for b in br if b.get("answer") is not None]
    opn = [b for b in br if b.get("answer") is None]
    counts = {}
    for b in ans:
        counts[b["answer"]] = counts.get(b["answer"], 0) + 1
    ranked = sorted(counts.values(), reverse=True)
    top = ranked[0] if ranked else 0
    second = ranked[1] if len(ranked) > 1 else 0
    return {"br": br, "ans": ans, "open": opn, "counts": counts, "top": top, "second": second,
            "calls": int(st.get("calls", 0) or 0), "tok": int(st.get("tok", 0) or 0)}


def _room(v):
    # A: the heard state selects the protocol (route by state)
    if v["calls"] >= CALLS_MAX - 1 or v["tok"] >= TOK_MAX - 2500:
        return "overload"
    if not v["ans"]:
        return "deficit"
    if v["top"] >= 2 and v["top"] > v["second"]:
        return "stable"
    if len(v["counts"]) == 1 and v["top"] == 1:
        b = v["ans"][0]
        if not b.get("errors") and not b.get("restarts"):
            return "stable"
    return "uncertainty"


def _bid(b):
    return b.get("id", 0)


def _best_open(v, exclude=()):
    # the open branch closest to an answer: fewest errors, then most progress
    cand = [b for b in v["open"] if _bid(b) not in exclude]
    if not cand:
        return None
    return sorted(cand, key=lambda b: (_nerr(b), -int(b.get("calls") or 0), _bid(b)))[0]


def _nerr(b):
    e = b.get("errors")
    return len(e) if isinstance(e, (list, tuple)) else int(e or 0)


def _budget_left(v, calls=3, tok=4000):
    return v["calls"] <= CALLS_MAX - calls and v["tok"] <= TOK_MAX - tok


def _heal_or_step(b):
    # K, P3 / White Dragon: repair only the part that differs (a branch stuck in errors), else its next step
    if _nerr(b) >= 2 and not b.get("restarts"):
        return ("restart", _bid(b))
    return ("step", _bid(b))


def _house(st, start="blind", second="blind", cross=False):
    v = _see(st)
    room = _room(v)
    br = v["br"]
    if not br:
        return None
    # ---- room: overload (Law 6 graceful landing; Law 4: no further spending without need)
    if room == "overload":
        if v["ans"]:
            return ("commit",)
        b = _best_open(v, exclude=(0,) if start in ("blind", "reuse") and len(br) > 1 else ())
        return ("step", _bid(b)) if b else None
    # ---- room: stable (G reached; Law 4 withholding is the move)
    if room == "stable":
        return ("commit",)
    # ---- room: deficit (nothing answered: land the first particle where the lack is)
    if room == "deficit":
        if v["calls"] == 0 and v["tok"] == 0:
            if start == "blind":
                return ("blind", _bid(br[0]))          # Law 2: one call, keys only, runtime computes
            if start == "reuse":
                return ("reuse", _bid(br[0]))          # inherit the stored plan (O trace), zero calls
            return ("step", _bid(br[0]))
        if start in ("blind", "reuse"):
            ids = {_bid(b) for b in br}
            if 1 not in ids and len(br) < 3 and _budget_left(v, 2, 3000):
                # the plan slot did not land: a second blind plan on a fresh slot (Law 2 again)
                return ("blind", 1) if start == "reuse" else ("new",)
            b = _best_open(v, exclude=(0,)) or _best_open(v)
        else:
            b = _best_open(v)
        return _heal_or_step(b) if b else None
    # ---- room: uncertainty (P8 triggered vote of futures; Law 5 cross)
    opn = v["open"]
    if opn and v["calls"] > 0:
        b = _best_open(v, exclude=(0,) if start in ("blind", "reuse") else ())
        if b is not None:
            if cross and v["ans"]:
                maj = max(v["ans"], key=lambda a: (v["counts"][a["answer"]], -_nerr(a)))
                if _bid(maj) != _bid(b):
                    return ("cross", _bid(b), _bid(maj))
            return _heal_or_step(b)
    if len(br) < 3 and _budget_left(v):
        if second == "blind":
            return ("blind", len(br))                  # an independent keys-only future on a fresh slot
        return ("new",)
    return ("commit",)


# Program 1: reuse_blind_house
# Rooms: deficit (no answer; calls == 0 -> reuse; plan missing -> blind on slot 1) · stable (commit) ·
#        uncertainty (P8: fresh blind slot, else step the open branch) · overload (commit / closest branch).
# Chain: V see branches -> A room -> K INHERIT(stored plan, U-trace) -> BLIND(keys, Law 2) -> VOTE(P8) -> O ids -> G commit.
# Laws: 0, 1, 2, 3 (P3 restart), 4 (commit at stability), 6.
# Invariant: no model call is spent once the answer is stable · check: the room reads stable => the action is commit.
def reuse_blind_house(st):
    return _house(st, start="reuse", second="blind")


# Program 2: blind_house
# Rooms: deficit (calls == 0 -> blind slot 0; else a fresh ReAct attempt) · stable (commit) ·
#        uncertainty (P8 triggered: a second blind plan on a fresh slot) · overload (commit).
# Chain: V -> A -> K BLIND(keys only; deterministic runtime computes values) -> VOTE(P8 on alarm) -> O -> G commit.
# Laws: 0, 1, 2, 4, 6.  Invariant: at most one model call per blind branch · check: blind only on unused slots.
def blind_house(st):
    return _house(st, start="blind", second="blind")


# Program 3: blind_cross_house
# Rooms: as blind_house, but uncertainty opens a fresh ReAct attempt and then CROSSes it with the majority answer.
# Chain: V -> A -> K BLIND -> NEW -> CROSS(Law 5: send only the other answer, what the branch cannot derive) -> O -> G.
# Laws: 0, 2, 4, 5, P8 triggered.  Invariant: cross only between two different branches · check: src != b.
def blind_cross_house(st):
    return _house(st, start="blind", second="new", cross=True)


# Program 4: react_vote_house
# Rooms: deficit (step branch 0; P3 restart of a branch with >= 2 errors) · stable (commit at once: Law 4) ·
#        uncertainty (P8 triggered: open one more attempt only when the answer came through errors or disagrees) ·
#        overload (commit).
# Chain: V -> A -> K STEP / HEAL(P3) -> VOTE(P8 triggered) -> O errors trace -> G commit.
# Laws: 0, 3 (repair only the failing branch), 4, 6.  Invariant: never more than 3 branches · check: len(br) < 3 before new.
def react_vote_house(st):
    return _house(st, start="step", second="new")


# Program 5: tiger_blind
# Tiger (U104: the closest, precise path): blind on slot 0, commit the first answer whatever its room (Law 4 at its
# strongest: no second future); if the plan slot did not answer, one fresh blind slot, then the closest open branch.
# Rooms: deficit / landed (any answer) / overload.  Chain: V -> A -> K BLIND -> G commit.  Laws: 2, 4, 6.
# Invariant: tokens of the task <= one blind call + one fallback · check: commit whenever any answer exists.
def tiger_blind(st):
    v = _see(st)
    br = v["br"]
    if not br:
        return None
    if v["ans"]:
        return ("commit",)
    if v["calls"] == 0 and v["tok"] == 0:
        return ("blind", _bid(br[0]))
    ids = {_bid(b) for b in br}
    if 1 not in ids and len(br) < 3 and _budget_left(v, 2, 3000):
        return ("blind", 1)
    b = _best_open(v, exclude=(0,)) or _best_open(v)
    return ("step", _bid(b)) if b else ("commit",)


MOVES = {
    "reuse_blind_house": reuse_blind_house,
    "blind_house": blind_house,
    "blind_cross_house": blind_cross_house,
    "react_vote_house": react_vote_house,
    "tiger_blind": tiger_blind,
}
