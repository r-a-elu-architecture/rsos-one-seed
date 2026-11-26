"""A7 arms. PREREGISTRATION_A7.md section 3. One loop for every arm: only the representation of the plan changes.

B2   M*: the market's most efficient setup for the same agents. One planner call writes the whole task as JSON Patch
     (RFC 6902) with literal values the model computed from the full state it is shown; one audit call; the same
     integrity layer (three copies, green-dot check before every step, restore from the snapshot at 0 calls).
X5r  RSOS assembly line exactly as A5's X5 (operations; the planner sees the lines each request names).
X5b  RSOS blind: the same as X5r, but the planner sees no values at all, only the requests.

Every arm: the runtime executes the plan on every copy; the audit selection is the same harness rule for every arm
(by request kind and a seeded 1-in-4 sample, never by the arm's own output, except 'no change', which is a result).
A5 files are imported, never changed.
"""

import hashlib
import json
import os
import re
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import a1_agents as A                      # noqa: E402
import a3b_hologram as H                   # noqa: E402
import a5_arms as X                        # noqa: E402
import a5_llm as L                         # noqa: E402

ARMS = ("B2", "X5r", "X5b", "B2s")      # B2s (A8): M* told to track the state explicitly
_wlock = threading.Lock()

# ---------------------------------------------------------------- audit selection: one harness rule for all arms

_ORACLE = None


def request_kind(req):
    """Harness classifier of a request (generator templates). Never shown to, or used by, an arm's planner."""
    global _ORACLE
    if _ORACLE is None:
        import a5_run
        _ORACLE = a5_run.oracle_ops
    return _ORACLE(req).split()[0]


def audit_step(set_name, seed, k, req, no_change):
    if no_change or request_kind(req) in X.RISK_OPS:
        return True
    return int(hashlib.sha256(f"{set_name}:{seed}:{k}".encode()).hexdigest(), 16) % 4 == 0


# ---------------------------------------------------------------- think control (A7b): applied to every arm alike

def thinking(mode):
    """mode 'default' or 'off'. 'off' sets MAX_THINKING_TOKENS=0 for every CLI call of the process."""
    if mode == "off":
        base = L.clean_env

        def env():
            e = base()
            e["MAX_THINKING_TOKENS"] = "0"
            return e
        L.clean_env = env


# ---------------------------------------------------------------- B2: JSON Patch

B2_SYS = ("You are the PLANNER in a pipeline that edits a configuration state of lines 'service.field = value'. You "
          "receive the current state and all change requests of one task, numbered; they are applied in order, each "
          "on the result of the previous one. For each request write a line '#<number>' and then one JSON Patch "
          "(RFC 6902) array on one line, with the exact final values: "
          "[{\"op\": \"replace\", \"path\": \"/auth.retries\", \"value\": \"5\"}]. Use \"replace\" to change a "
          "line, \"add\" to add a new line, \"remove\" to delete one. Resolve conditions, arithmetic, copies and "
          "owner transfers yourself. Output only the numbered patches.")
B2_SYS_S2 = " A request may begin with 'Worker-computed:'; treat it like any other request."
B2_AUDIT = ("You are the AUDITOR in a pipeline that edits a configuration state of lines 'service.field = value'. A "
            "planner wrote a JSON Patch for each change request and a deterministic runtime applied it. Check that "
            "the result implements the request exactly: every line the request changes, with the right value, and "
            "no other line. " + X.PALACE)
B2S_NOTE = (" Before each patch, work out the current value of every line the request reads or matches, applying "
            "all earlier patches of this task in order; only then write the patch.")
X5B_NOTE = (" You see no state values, only the requests: name keys and relations; the runtime reads and computes "
            "every value.")


def parse_patch(body, state):
    t = body.strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t.strip(), flags=re.M).strip()
    i, j = t.find("["), t.rfind("]")
    if i < 0 or j < i:
        raise X.OpError("no JSON Patch array")
    try:
        arr = json.loads(t[i:j + 1])
    except ValueError as e:
        raise X.OpError(f"invalid JSON: {str(e)[:60]}")
    if not isinstance(arr, list):
        raise X.OpError("not a JSON Patch array")       # [] is a valid patch: the request changes nothing
    ops = []
    for p in arr:
        if not isinstance(p, dict) or "op" not in p or "path" not in p:
            raise X.OpError("patch entry without op/path")
        k = p["path"].strip().lstrip("/").replace("/", ".")
        k = X.key_of(k)
        if p["op"] in ("replace", "add"):
            if "value" not in p:
                raise X.OpError(f"{p['op']} without value")
            v = str(p["value"]).strip()
            if X.is_keyref(v, state):
                raise X.OpError(f"value '{v}' is a key, not a value")
            ops.append(("SET", k, v))
        elif p["op"] == "remove":
            ops.append(("DEL", k))
        else:
            raise X.OpError(f"unsupported op '{p['op']}'")
    return ops


def patch_text(ops):
    return json.dumps([{"op": "remove", "path": "/" + o[1]} if o[0] == "DEL" else
                       {"op": "replace", "path": "/" + o[1], "value": o[2]} for o in ops], separators=(",", ":"))


# ---------------------------------------------------------------- the one loop

def run_plan(arm, set_name, seed, tag=None, planner=None, auditor=None, think="default"):
    assert arm in ARMS
    task = A.make_task(seed)
    truths = task["truths"]
    plan = A.drift_plan(task, truths)
    n = len(task["requests"])
    if arm in ("B2", "B2s"):
        psys = B2_SYS + (B2S_NOTE if arm == "B2s" else "") + (B2_SYS_S2 if set_name == "S2" else "")
        asys = B2_AUDIT + X.X5_AUDIT
    else:
        psys = X.planner_system("X3", set_name) + X.X5_PLAN + (X5B_NOTE if arm == "X5b" else "")
        asys = X.auditor_system("X3", set_name) + X.X5_AUDIT
    log, msgs, calls = [], [], []
    t_start = time.time()
    ctx = {"step": -1, "attempt": 0}

    def send(step, a, b, text, kind="msg"):
        msgs.append({"step": step, "attempt": ctx["attempt"], "from": a, "to": b, "text": text,
                     "tok": A.ntok(text), "bpe": H.bpe(text), "bytes": len(text.encode()), "kind": kind})

    def call(role, system, prompt):
        fake = planner if role == "planner" else auditor
        if fake is not None:
            text, rec = fake(prompt, ctx), {"in": 0, "cache_w": 0, "cache_w5m": 0, "cache_w1h": 0, "cache_r": 0,
                                            "out": 0, "think": 0, "sec": 0.0, "cost": 0.0}
        else:
            text, _, rec = L.llm(system, prompt, None, log)
        calls.append({**rec, "role": role, "step": -1, "attempt": ctx["attempt"]})
        return text

    init = dict(task["init"])
    render = patch_text if arm in ("B2", "B2s") else X.ops_text
    ops_by, ops_txt, approved, feedback = {}, {}, set(), {}
    invalid_ops = 0
    attempts = {k: 0 for k in range(n)}
    audit_log = []
    todo = list(range(n))
    for rnd in range(A.MAX_RETRY + 1):
        ctx["attempt"] = rnd
        if not todo:
            break
        lines = []
        for k in todo:
            block = f"#{k + 1} {task['requests'][k]}"
            if arm == "X5r":
                sel = X.select_lines(task["requests"][k], init)
                if sel:
                    block += "\nLines: " + " ".join(sel)
            if k in feedback:
                block += f"\nRejected before: {feedback[k]}\nPrevious operations: {ops_txt.get(k, '(invalid)')}"
            lines.append(block)
        head = ("State:\n" + A.text_of(init) + "\n\n") if arm in ("B2", "B2s") else ""
        ptext = call("planner", psys, head + "Change requests:\n" + "\n\n".join(lines))
        parts = X.split_steps(ptext, n)
        for k in todo:
            attempts[k] += 1
            body = parts.get(k + 1)
            try:
                if body is None:
                    raise X.OpError("no operations for this step")
                ops_by[k] = parse_patch(body, init) if arm in ("B2", "B2s") else X.parse_ops(body)
                ops_txt[k] = render(ops_by[k])
                send(k, "planner", "runtime", f"#{k + 1}\n" + ops_txt[k])
            except X.OpError as e:
                invalid_ops += 1
                ops_by.pop(k, None); ops_txt.pop(k, None)
                feedback[k] = f"the runtime rejected the output: {e}"
                send(k, "runtime", "planner", f"#{k + 1} invalid: {e}", kind="invalid")
        steps, _, _ = X.simulate(task, plan, dict(ops_by))
        for k in todo:
            if k in ops_by and steps[k]["error"]:
                invalid_ops += 1
                feedback[k] = f"the runtime rejected the operations: {steps[k]['error']}"
                send(k, "runtime", "planner", f"#{k + 1} invalid: {steps[k]['error']}", kind="invalid")
                ops_by.pop(k)
        steps, _, _ = X.simulate(task, plan, dict(ops_by))
        cand = [k for k in todo if k in ops_by]
        sel_audit = [k for k in cand if audit_step(set_name, seed, k, task["requests"][k],
                                                   not X.changes(steps[k]["pre"], steps[k]["new"]))]
        for k in cand:
            if k not in sel_audit:
                approved.add(k)
        if sel_audit:
            blocks = []
            for k in sel_audit:
                s = steps[k]
                ch = X.changes(s["pre"], s["new"], palace=True)
                src = ", ".join(f"{X.code(x)}={s['pre'][x]}" for x in s["srcs"] if x in s["pre"]) or "(none)"
                blocks.append(f"#{k + 1} {task['requests'][k]}\nOps: " + ops_txt[k].replace("\n", " ; ") +
                              "\nResult: " + ("; ".join(ch) if ch else "(no change)") + f"\nSources: {src}" +
                              "\nBefore: " + X.before_lines(task["requests"][k], ops_by[k], s["pre"], palace=True))
            ap = "Steps:\n" + "\n\n".join(blocks)
            send(-1, "runtime", "auditor", ap)
            atext = call("auditor", asys, ap)
            ver = X.parse_verdicts(atext)
            if not any(k + 1 in ver for k in sel_audit) and len(ver) == len(sel_audit) and \
                    sorted(ver) == list(range(1, len(sel_audit) + 1)):
                ver = {k + 1: ver[i + 1] for i, k in enumerate(sel_audit)}
            send(-1, "auditor", "runtime", atext.strip())
            audit_log.append({"round": rnd, "steps": sel_audit, "text": atext.strip()[:2000]})
            for k in sel_audit:
                good, reason = ver.get(k + 1, (False, "no verdict for this step"))
                if good:
                    approved.add(k)
                else:
                    feedback[k] = reason
                    ops_by.pop(k, None)
        todo = [k for k in range(n) if k not in approved]
    final_ops = {k: v for k, v in ops_by.items() if k in approved}
    steps, drift_events, copies = X.simulate(task, plan, final_ops,
                                             send=lambda st, a, b, t, kd: send(st, a, b, t, kd))
    step_log = []
    for st in range(n):
        expect = dict(steps[st]["pre"])
        for k in set(truths[st]) | set(truths[st + 1]):
            if k not in truths[st + 1]:
                expect.pop(k, None)
            elif truths[st].get(k) != truths[st + 1][k]:
                expect[k] = truths[st + 1][k]
        ok = st in final_ops
        rec = {"step": st, "ok": ok, "correct": steps[st]["new"] == expect, "attempts_n": attempts[st],
               "kind": request_kind(task["requests"][st]), "ops": ops_txt.get(st) if ok else None,
               "audited": ok and audit_step(set_name, seed, st, task["requests"][st],
                                            not X.changes(steps[st]["pre"], steps[st]["new"]))}
        if ok and not rec["correct"]:
            rec["audit_miss"] = "approved" if rec["audited"] else "unsampled"
        step_log.append(rec)
    final = A.state_of_text(copies["planner"])
    cs = [A.state_of_text(c) for c in copies.values()]
    truth = task["final"]
    keys = set(truth) | set(final)
    acc = sum(final.get(k) == truth.get(k) for k in keys) / len(keys)
    for e in drift_events:
        e["silent_in_final"] = final.get(e["key"]) != e["true"]
        e["in_any_copy_final"] = any(c.get(e["key"]) != e["true"] for c in cs)
    success = final == truth
    res = {"arm": arm, "cond": arm, "seed": seed, "tag": tag, "think": think, "success": success, "line_acc": acc,
           "replica_success": all(dict.__eq__(truth, c) for c in cs),
           "final_errors": sorted(k for k in keys if final.get(k) != truth.get(k)), "final_state": final,
           "steps_failed": sum(1 for s in step_log if not s["ok"]),
           "steps_wrong": sum(1 for s in step_log if s["ok"] and not s["correct"]), "invalid_ops": invalid_ops,
           "n_msgs": len(msgs), "n_calls": len(calls),
           "channel_tok": sum(m["tok"] for m in msgs), "channel_bpe": sum(m["bpe"] for m in msgs),
           "channel_bytes": sum(m["bytes"] for m in msgs),
           "billed_tok": sum(A.billed(c) for c in calls), "out_tok": sum(c["out"] for c in calls),
           "think_tok": sum(c.get("think", 0) for c in calls),
           "in_tok": sum(c["in"] + c["cache_w"] + c["cache_r"] for c in calls),
           "cost_usd": sum(c["cost"] or 0 for c in calls), "wall_sec": time.time() - t_start,
           "drift": drift_events, "steps": step_log, "audits": audit_log, "calls_full": calls,
           "per_msg": [{k: m[k] for k in ("step", "attempt", "from", "to", "tok", "bpe", "bytes", "kind")}
                       for m in msgs]}
    tr = os.environ.get("A7_TRANSCRIPTS")
    if tr:
        with _wlock:
            with open(tr, "a") as f:
                f.write(json.dumps({"arm": arm, "set": set_name, "seed": seed, "tag": tag, "think": think,
                                    "msgs": msgs, "calls": log, "steps": step_log}) + "\n")
    print(f"{set_name} {arm} {seed} think={think} success={success} acc={acc:.3f} calls={len(calls)} "
          f"out={res['out_tok']} think_tok={res['think_tok']} inv={invalid_ops} wrong={res['steps_wrong']} "
          f"fail={res['steps_failed']} wall={res['wall_sec']:.0f}s", flush=True)
    return res, task
