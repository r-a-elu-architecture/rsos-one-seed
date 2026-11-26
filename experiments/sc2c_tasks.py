"""SC2-C: the control condition for SC2 (PREREGISTRATION_SC2.md, amendment 3).

The same tasks as SC2 (same beacon seeds, same generator, same state changes, same truths and drift), with one
difference: every FLOW request names its objects instead of describing them, so a planner does not have to find them.

    SC2:    "Move every object owned by rover 1 cell right (x plus 1, capped at 9)."
    SC2-C:  "Move cup, box and lamp 1 cell right (x plus 1 each, capped at 9)."

The objects listed are exactly those the FLOW request moves at that step (the generator's truth), in object order.
Everything else is byte-identical to SC2. If one-call JSON Patch fails far more often on the SC2 wording, the cause is
finding the objects in a state that has changed since the start, not computing their values (Q10).
"""

import re

import a1_agents as A
import sc2_tasks as S2

CELLS = {"SC2C": (56, 4, 50)}
SEEDS = {"SC2C": S2.SEEDS["SC2"]}
NAMED_REQ = r"^Move ((?:[a-z]+, )*[a-z]+(?: and [a-z]+)?) (\d) cells? (right|up) \((\S+) plus (\d) each, capped at 9\)\.$"


def _names(objs):
    return objs[0] if len(objs) == 1 else ", ".join(objs[:-1]) + " and " + objs[-1]


def make_task(seed, **kw):
    t = S2.make_task(seed, **kw)
    reqs = []
    for k, r in enumerate(t["requests"]):
        m = re.match(S2.FLOW_REQ, r)
        if not m:
            reqs.append(r)
            continue
        robot, n, d, field = m.group(1), m.group(2), m.group(3), m.group(4)
        before = t["truths"][k]
        objs = [o for o in S2.SC.OBJECTS if before.get(f"{o}.owner") == robot and f"{o}.{field}" in before]
        if not objs:                                  # nothing to move: keep a request that changes nothing
            reqs.append(r)
            continue
        reqs.append(f"Move {_names(objs)} {n} cell{'s' if n != '1' else ''} {d} ({field} plus {n} each, capped at 9).")
    t["requests"] = reqs
    return t


def _oracle(m):
    objs = re.split(r", | and ", m[1])
    return "\n".join(f"INHERIT {o}.{m[4]} {o}.{m[4]} +{m[2]} CAP 9" for o in objs)


def patch(cell="SC2C"):
    import a5_run as R5
    S2.patch("SC2")
    A.make_task = make_task
    if not any(rx == NAMED_REQ for rx, _ in R5.ORACLE):
        R5.ORACLE.append((NAMED_REQ, _oracle))
