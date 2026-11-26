# RSOS decision programs, domain 1: AI agents solving tool-use tasks (CONF4, R1).
# Host = computer: VAKOG order V (see the branches) -> A (the room selects the protocol) -> K (act in order)
# -> O (trace: errors, restarts, which slot carried which answer) -> G (commit = the taste of the whole chain).
# Every program is a HOUSE: rooms routed by the host's state (U5, U64, U69), one composed chain per room.
# Pure functions of st; Python standard library only.

CALL_CAP = 12
TOK_CAP = 16000


def _nerr(b):
    e = b.get("errors", 0)
    if isinstance(e, (list, tuple, dict, set)):
        return len(e)
    try:
        return int(e or 0)
    except (TypeError, ValueError):
        return 0


def _see(st):
    # V: the image of the task's state (read scope, Law 1': only answers, budget, errors)
    br = list(st.get("br") or [])
    answers = {}
    for b in br:
        a = b.get("answer")
        if a is not None:
            answers.setdefault(a, []).append(b)
    best, best_n = None, 0
    for a, bs in answers.items():
        if len(bs) > best_n:
            best, best_n = a, len(bs)
    open_br = [b for b in br if b.get("answer") is None]
    calls = st.get("calls", 0) or 0
    tok = st.get("tok", 0) or 0
    return br, answers, best, best_n, open_br, calls, tok


def _free_slot(br):
    # a branch slot not yet used (slots 0..2); None when all three are taken
    used = set(b.get("id") for b in br)
    for s in range(3):
        if s not in used:
            return s
    return None


def _deficit(calls, tok):
    # overload / deficit room trigger: the task's own budget is near its end (U103)
    return calls >= CALL_CAP - 2 or tok >= TOK_CAP - 2500


def _heal_or_step(open_br):
    # K inside the working room. White Dragon (U90, P3): repair only the failing part:
    # a branch with >= 2 error observations and no restart yet is restarted; otherwise the Tiger path (U104):
    # the closest, most precise step = the open branch with the fewest errors and the fewest calls.
    for b in open_br:
        if _nerr(b) >= 2 and (b.get("restarts", 0) or 0) == 0:
            return ("restart", b.get("id"))
    b = min(open_br, key=lambda x: (_nerr(x), x.get("calls", 0) or 0))
    return ("step", b.get("id"))


def _house(st, start, trust_single):
    br, answers, best, best_n, open_br, calls, tok = _see(st)
    # A: the room is selected by state; G: commit is the result room
    # Room RESOLVED (stable): two agreeing answers -> commit (Law 4: further calls change nothing).
    if best_n >= 2:
        return ("commit",)
    # Room DEFICIT (overload): budget near its end -> land the answer we hold, or the cheapest single step.
    if _deficit(calls, tok):
        if best is not None:
            return ("commit",)
        if open_br:
            return ("step", min(open_br, key=lambda x: (_nerr(x), x.get("calls", 0) or 0)).get("id"))
        return ("commit",)
    # Room SEED (nothing spent yet): the start operator (blind plan, or the inherited plan).
    if calls == 0 and not answers:
        return start
    # Room SINGLE (one answer, no disagreement).
    if len(answers) == 1 and best_n == 1:
        holder = answers[best][0]
        clean = _nerr(holder) == 0
        if trust_single and clean:
            return ("commit",)            # Law 4: withholding further calls is a move
        # P8 triggered: the structure reads uncertainty (errors on the answering branch, or trust off):
        # one more future written blind (Law 2) on a free slot; an open branch is stepped instead if present.
        if open_br:
            return _heal_or_step(open_br)
        s = _free_slot(br)
        if s is not None:
            return ("blind", s)
        return ("commit",)
    # Room UNCERTAINTY (answers disagree): P8 vote of futures, the third voice written blind.
    if len(answers) >= 2:
        if open_br:
            # fuse (P4): the open branch is told the leading answer only if one leads; else it steps on its own
            return _heal_or_step(open_br)
        s = _free_slot(br)
        if s is not None:
            return ("blind", s)
        return ("commit",)
    # Room WORKING (no answer yet, calls spent): heal the failing part, or the Tiger step.
    if open_br:
        # Law 2 rescue: a ReAct branch with errors and no restart left is replaced by a blind plan on a free slot
        stuck = [b for b in open_br if _nerr(b) >= 2 and (b.get("restarts", 0) or 0) >= 1]
        s = _free_slot(br)
        if stuck and len(stuck) == len(open_br) and s is not None:
            return ("blind", s)
        return _heal_or_step(open_br)
    s = _free_slot(br)
    if s is not None:
        return ("blind", s)
    return ("commit",)


# house_blind_trigvote
# Rooms: SEED (calls == 0, no answer) -> blind plan on slot 0 | SINGLE (one answer) -> commit if its branch
#   is clean, else P8 triggered second blind future | UNCERTAINTY (answers disagree) -> third future, blind |
#   RESOLVED (2 agree) -> commit | DEFICIT (calls >= 10 or tokens >= 13,500) -> commit what is held / one step |
#   WORKING -> White Dragon restart of the failing branch, else Tiger step.
# Chain (V->A->K->O->G): see answers+budget -> room -> blind plan / heal / step -> trace errors -> commit.
# Laws: Law 2 (the model sends only keys; the runtime computes every value), Law 4 (commit as soon as more calls
#   cannot change the result; withholding is a move), Law 3 / P3 (restart only the failing branch), P8 triggered
#   (vote only where the trace reads uncertainty), Law 1' (reads only answers, budget, error counts), Law 0.
# Invariant: never exceeds the task budget (deficit room commits before the cap); never discards a held majority.
# Check: every commit holds an answer or the budget is spent; every extra branch follows an uncertainty read.
def house_blind_trigvote(st):
    return _house(st, ("blind", 0), trust_single=True)


# house_reuse_inherit
# Rooms: as house_blind_trigvote, but SEED lands the inherited plan of the same task shape ("reuse", U152 infinite
#   seed / inherit the trace) at zero model calls; a clean inherited answer is committed at once.
# Chain: see -> room -> reuse (inherit) -> trace -> commit; when no plan exists the host falls back to its
#   standard, and the next decision continues in the WORKING room (heal / step / blind rescue).
# Laws: Law 5 (send nothing the host already holds: the stored plan), Law 2, Law 4, P3, P8 triggered, Law 0.
# Invariant: zero-call answer first; any later call only on a read of uncertainty or no answer.
# Check: tokens on a reused task = 0 when the inherited answer is clean.
def house_reuse_inherit(st):
    return _house(st, ("reuse", 0), trust_single=True)


# house_reuse_verify
# Rooms: SEED -> reuse (zero calls) | SINGLE -> always one blind verification future (P8 always armed after an
#   inherited answer: two independent signs, U125 two-sign) | UNCERTAINTY -> third blind future | RESOLVED -> commit |
#   DEFICIT -> commit held | WORKING -> heal / Tiger step.
# Chain: see -> room -> reuse -> blind check (Law 2) -> vote -> commit.
# Laws: Law 5 + Law 2 + P8 vote of futures + U125 two-sign, Law 4 in DEFICIT, Law 0.
# Invariant: an answer is committed only with two agreeing signs, unless the budget room ends the task.
# Check: committed answers carry >= 2 agreeing branches except in the deficit room.
def house_reuse_verify(st):
    return _house(st, ("reuse", 0), trust_single=False)


# house_blind_twosign
# Rooms: SEED -> blind plan on slot 0 | SINGLE -> always a second blind future (two-sign, U125) |
#   UNCERTAINTY -> third blind future (P8) | RESOLVED -> commit | DEFICIT -> commit held | WORKING -> heal / step.
# Chain: see -> room -> blind -> blind -> (blind) -> commit: self-consistency rebuilt on Law 2 (one call per voice).
# Laws: Law 2 (each voice is one call, values computed by the runtime), P8 vote of futures, Law 4 (stops at the first
#   2-of-n agreement), Law 0.
# Invariant: at most 3 voices and at most 3 model calls on the clean path.
# Check: accuracy >= single blind; tokens far below ReAct self-consistency.
def house_blind_twosign(st):
    return _house(st, ("blind", 0), trust_single=False)


# react_lion_tiger_heal
# Rooms: WORKING (branch 0 open) -> Tiger step of the cleanest open branch, White Dragon restart on >= 2 errors |
#   STUCK (every open branch has errors after its restart) -> Law 2 rescue: blind plan on a free slot |
#   ANSWER -> commit at once if the answering branch is clean (Law 4), else P8 triggered blind future |
#   UNCERTAINTY -> blind third voice | DEFICIT -> commit held / cheapest step.
# Chain: see -> room -> step / restart (heal only the failing part) -> blind rescue -> commit.
# Laws: Law 3 / P3 (repair only the part that differs), Law 2 (rescue), Law 4, P8 triggered, Law 0.
# Invariant: the program stays on the standard's own path (ReAct) while it works; it deviates only at a read need.
# Check: never worse than ReAct where ReAct answers cleanly; recovers the tasks where ReAct stalls on errors.
def react_lion_tiger_heal(st):
    br = list(st.get("br") or [])
    if (st.get("calls", 0) or 0) == 0 and not any(b.get("answer") is not None for b in br):
        return ("step", br[0].get("id") if br else 0)
    return _house(st, ("step", 0), trust_single=True)


MOVES = {
    "house_blind_trigvote": house_blind_trigvote,
    "house_reuse_inherit": house_reuse_inherit,
    "house_reuse_verify": house_reuse_verify,
    "house_blind_twosign": house_blind_twosign,
    "react_lion_tiger_heal": react_lion_tiger_heal,
}
