"""ENGINE3 guards around the frozen B2 arm (JSON Patch). The frozen files (a5_*, a7_arms, a7_run) are not changed:
a guarded planner is passed to a7_arms.run_plan through its `planner` hook.

Guards (corpus ENGINE3_PACKAGE; causes named by AGENTS2 and SC2):
  LATE      steps in the second half of the plan are re-planned alone on the state they will actually meet
  DISAGREE  a second independent draft; steps whose patches differ are re-planned alone
  READY     a step whose patch does not parse, or names a key absent from the state it meets, is re-planned alone
Re-planning alone = one call with the current state (after the planner's own earlier patches) and one request.

Usage (owner's machine):  python3 experiments/a7_guard.py <set> <seed> <guards e.g. LATE,READY> [tag]
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import a1_agents as A          # noqa: E402
import a5_arms as X            # noqa: E402
import a5_llm as L             # noqa: E402
import a7_arms as S            # noqa: E402

GUARDS = ("LATE", "DISAGREE", "READY")


def apply_ops(state, ops):
    s = dict(state)
    for o in ops:
        if o[0] == "SET":
            s[o[1]] = o[2]
        else:
            s.pop(o[1], None)
    return s


def norm(body):
    return re.sub(r"\s+", "", body or "")


def assemble(parts, n):
    return "\n".join(f"#{k}\n{parts.get(k, '')}" for k in range(1, n + 1))


def make_planner(seed, set_name, guards, costs, llm=None):
    """Returns a planner(prompt, ctx) for run_plan, and records every real call's cost in `costs`."""
    llm = llm or (lambda system, prompt: L.llm(system, prompt, None, None))
    task = A.make_task(seed)
    reqs, n = task["requests"], len(task["requests"])
    system = S.B2_SYS + (S.B2_SYS_S2 if set_name == "S2" else "")

    def call(prompt):
        text, _, rec = llm(system, prompt)
        costs.append(rec)
        return text

    def planner(prompt, ctx):
        first = call(prompt)
        if ctx.get("attempt", 0) > 0 or not guards:
            return first                                   # retries: the frozen loop handles them
        parts = X.split_steps(first, n)
        flagged = set()
        if "LATE" in guards:
            flagged |= {k for k in range(n // 2 + 1, n + 1)}
        if "DISAGREE" in guards:
            other = X.split_steps(call(prompt), n)
            flagged |= {k for k in range(1, n + 1) if norm(parts.get(k)) != norm(other.get(k))}
        state = dict(task["init"])
        for k in range(1, n + 1):
            body = parts.get(k)
            ok = True
            try:
                ops = S.parse_patch(body, state) if body is not None else None
                if ops is None:
                    ok = False
                elif "READY" in guards and any(o[0] == "DEL" and o[1] not in state for o in ops):
                    ok = False
            except X.OpError:
                ops, ok = None, False
            if (k in flagged) or ("READY" in guards and not ok):
                alone = call("State:\n" + A.text_of(state) + "\n\nChange requests:\n#1 " + reqs[k - 1])
                body2 = X.split_steps(alone, 1).get(1)
                try:
                    ops2 = S.parse_patch(body2, state) if body2 is not None else None
                except X.OpError:
                    ops2 = None
                if ops2 is not None:
                    parts[k], ops = body2, ops2
            if ops is not None:
                state = apply_ops(state, ops)
        return assemble(parts, n)
    return planner


def run(set_name, seed, guards, tag=None):
    import a7_run
    a7_run.setup(set_name)                                  # same set generator and timeouts as the frozen harness
    costs = []
    res, task = S.run_plan("B2", set_name, seed, tag=tag, planner=make_planner(seed, set_name, guards, costs))
    res["arm"] = res["cond"] = "B2g:" + ",".join(sorted(guards))
    for key, field in (("cost_usd", "cost"), ("out_tok", "out"), ("think_tok", "think")):
        res[key] = sum((c.get(field) or 0) for c in costs)
    res["guard_calls"] = len(costs)
    return res


if __name__ == "__main__":
    g = [x for x in sys.argv[3].split(",") if x] if len(sys.argv) > 3 else []
    assert all(x in GUARDS for x in g), g
    r = run(sys.argv[1], int(sys.argv[2]), g, sys.argv[4] if len(sys.argv) > 4 else None)
    out = os.environ.get("A7G_OUT", os.path.join(HERE, "..", "results", "engine3_results.jsonl"))
    with open(out, "a") as f:
        f.write(json.dumps({k: v for k, v in r.items() if k not in ("calls_full",)}) + "\n")
