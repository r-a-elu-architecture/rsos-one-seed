"""Composed RSOS moves for AI agents on tool-use tasks (domain 1).

Grammar: composition; the sequence of operators is the program, in VAKOG order
(see -> choose -> act -> trace -> result). Each operator is a small pure function of
the state view `st` (or of what the previous operator returned); each move is their
composition and returns ONE native action or None (None = no landing needed here).

Native actions: ("step", id), ("new",), ("restart", id), ("cross", id, src_id), ("commit",).
Branches are named by b["id"].
"""

CALLS_MAX = 12
TOK_MAX = 16000


# ---------------------------------------------------------------- operators
def see(st):
    """V: the image of the task now: branches split into answered / open, plus budget left."""
    br = list(st.get("br") or [])
    answered = [b for b in br if b.get("answer") is not None]
    open_ = [b for b in br if b.get("answer") is None]
    return {
        "br": br,
        "answered": answered,
        "open": open_,
        "calls_left": CALLS_MAX - int(st.get("calls", 0) or 0),
        "tok_left": TOK_MAX - int(st.get("tok", 0) or 0),
    }


def trace(v):
    """O: what each branch carries from before (errors, restarts), and the answer tally."""
    tally = {}
    for b in v["answered"]:
        a = str(b["answer"]).strip().lower()
        tally[a] = tally.get(a, 0) + 1
    v["tally"] = tally
    v["top"] = max(tally.values()) if tally else 0
    v["disagree"] = len(tally) >= 2
    v["err_answered"] = sum(len(b.get("errors") or []) for b in v["answered"])
    return v


def compress(v):
    """Many answers into one symbol: is there a majority (two or more agreeing)?"""
    v["consensus"] = v["top"] >= 2 and v["top"] > len(v["answered"]) - v["top"]
    return v


def contain(v):
    """Budget membrane: is the task near its bound (no room for another full step)?"""
    v["near_bound"] = v["calls_left"] <= 1 or v["tok_left"] <= 1500
    v["room_for_future"] = v["calls_left"] >= 4 and v["tok_left"] >= 5000
    return v


def heal_target(v):
    """P3 part check: the open branch whose own trace shows damage (>= 2 errors, not yet restarted)."""
    cands = [b for b in v["open"]
             if len(b.get("errors") or []) >= 2 and int(b.get("restarts", 0) or 0) == 0]
    if not cands or v["calls_left"] < 3:
        return None
    return max(cands, key=lambda b: (len(b.get("errors") or []), -int(b.get("calls", 0) or 0)))


def vote_trigger(v):
    """P8 triggered: a further future only where the structure reads uncertainty."""
    if v["open"] or len(v["br"]) >= 3 or not v["answered"] or not v["room_for_future"]:
        return False
    single_with_errors = len(v["answered"]) == 1 and v["err_answered"] > 0
    return v["disagree"] or single_with_errors


def overlay_source(v):
    """The answered branch whose trace is cleanest (fewest errors), carried across to another branch."""
    if not v["answered"]:
        return None
    return min(v["answered"], key=lambda b: (len(b.get("errors") or []), int(b.get("tok", 0) or 0)))


def beam_target(v):
    """Focus from below: the open branch closest to landing (fewest errors, most progress)."""
    if not v["open"] or v["calls_left"] < 1:
        return None
    return min(v["open"], key=lambda b: (len(b.get("errors") or []), -int(b.get("calls", 0) or 0)))


# ---------------------------------------------------------------- moves
# see > trace > compress > contain > commit: tally the answers, compress them into a majority;
# land "commit" when two attempts already agree, or when the budget membrane is reached and an
# answer exists (accuracy kept, tokens of further steps saved).
def m_commit(st):
    v = contain(compress(trace(see(st))))
    if v["consensus"]:
        return ("commit",)
    if v["near_bound"] and v["answered"]:
        return ("commit",)
    return None


# see > trace > heal > restart: read each open branch's own error trace; the one damaged
# (>= 2 errors, never restarted) is restarted afresh, only that part (P3 part repair).
def m_heal(st):
    v = contain(trace(see(st)))
    b = heal_target(v)
    return ("restart", b["id"]) if b is not None else None


# see > trace > contain > vote > new: a fresh future (temperature 0.7) only when the structure
# reads uncertainty (answers disagree, or the single answer came through errors) and the
# budget has room; otherwise the answer stands.
def m_vote(st):
    v = contain(trace(see(st)))
    return ("new",) if vote_trigger(v) else None


# see > trace > overlay > cross: the cleanest answered branch's answer is carried across into
# an open branch that is struggling (errors) or into the tie-breaker when answers disagree;
# that branch's next step checks it instead of searching from zero.
def m_cross(st):
    v = contain(trace(see(st)))
    src = overlay_source(v)
    if src is None or not v["open"] or v["calls_left"] < 1:
        return None
    struggling = [b for b in v["open"] if (b.get("errors") or [])]
    pool = struggling if struggling else (v["open"] if v["disagree"] else [])
    if not pool:
        return None
    b = max(pool, key=lambda x: (len(x.get("errors") or []), int(x.get("calls", 0) or 0)))
    if b["id"] == src["id"]:
        return None
    return ("cross", b["id"], src["id"])


# see > trace > beam > step: from below, the whole step goes to the open branch nearest to its
# answer (fewest errors, most progress) instead of a fixed branch order.
def m_beam(st):
    v = contain(trace(see(st)))
    b = beam_target(v)
    return ("step", b["id"]) if b is not None else None


MOVES = {
    "see>trace>compress>contain>commit": m_commit,
    "see>trace>heal>restart": m_heal,
    "see>trace>contain>vote>new": m_vote,
    "see>trace>overlay>cross": m_cross,
    "see>trace>beam>step": m_beam,
}
