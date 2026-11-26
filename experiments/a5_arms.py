"""A5 arms. PREREGISTRATION_A5.md section 3.

B1: the frozen H-dragon run (a3b_hologram.run_task with HDragon; S2 through a4_latent.run_one) with the Phase 0 fixed
call and the static output instruction moved into the system prompt.
X1, X1s, X2, X3: the planner writes RSOS operations, the RSOS runtime executes them on every copy, an auditor call
checks the result (every step in X1; risk-weighted plus 1 in 4 in the others). No worker call.
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
import a5_llm as L                         # noqa: E402
from a3b_hdragon import HDragon, KC, KEY, REG, REGI   # noqa: E402
from rsoslang import palace as PAL         # noqa: E402

_tl = threading.local()
_wlock = threading.Lock()
X_ARMS = ("X1", "X1s", "X2", "X3")
ARMS = ("B1",) + X_ARMS + ("X5",)
RISK_OPS = {"DEL", "INHERIT", "FUSE", "SCALE", "ROUTE", "REHOST"}


def calls_sink():
    if not hasattr(_tl, "calls"):
        _tl.calls = []
    return _tl.calls


# ---------------------------------------------------------------- B1: frozen H-dragon, fixed call, static first

def reorder(system, prompt):
    for suf in (A.W_P, A.C_OUT):
        if prompt.endswith("\n\n" + suf):
            return system + " " + suf, prompt[: -len(suf) - 2]
    return system, prompt


def b1_llm(system, prompt, schema=None, log=None):
    s, p = reorder(system, prompt)
    text, so, rec = L.llm(s, p, schema, None)
    if log is not None:
        log.append({"kind": "llm", "system": system[:40], "prompt": prompt, "moved_to_system": s != system,
                    "text": text, "structured": so, **rec})
    calls_sink().append(dict(rec))
    return text, so, rec


def install_b1():
    A.llm = b1_llm


def run_b1(set_name, seed, tag=None):
    _tl.calls = []
    if set_name == "S2":
        import a4_latent as A4
        res = A4.run_one("Hd", seed, tag=tag)
        task = A4._tl.task
    else:
        res = H.run_task(HDragon(), seed, tag=tag)
        task = None
    full = _tl.calls
    assert len(full) == len(res["per_call"])
    res["calls_full"] = [{**f, "role": p["role"], "step": p["step"], "attempt": p["attempt"]}
                         for f, p in zip(full, res["per_call"])]
    res["arm"] = "B1"
    return res, task


# ---------------------------------------------------------------- the RSOS runtime

class OpError(Exception):
    pass


GRAMMAR_V0 = ("RSOS operations, one per line (key = service.field):\n"
              "SET k v            k = v (a new key is added at the end)\n"
              "DEL k              remove line k\n"
              "INHERIT d s [+n] [CAP m]   d = s (+ n), at most m\n"
              "FUSE d a b [CAP m]         d = a + b, at most m\n"
              "SCALE k f [CAP m]          k = k x f, at most m\n"
              "ROUTE s = x : d v1 | v2    d = v1 if s equals x, else v2\n"
              "REHOST field a b           every line of that field whose value is a becomes b\n"
              "The runtime reads every value from its own copy and computes every result.")
GRAMMAR = ("RSOS ops, one per line, words separated by spaces (k = service.field): SET k v | DEL k | "
           "INHERIT d s [+n] [CAP m] (d = s+n, max m) | FUSE d a b [CAP m] (d = a+b) | SCALE k f [CAP m] (k = k*f) | "
           "ROUTE s = x : d v1 | v2 (d = v1 if s is x, else v2) | REHOST field a b (each <field> line equal to a "
           "becomes b). INHERIT copies any value (numbers, owners, regions, levels). The runtime reads and computes every "
           "value.")      # amendment 1 (compact text, same ops); amendment 3 (INHERIT copies any value)
PALACE = ("Palace codes: a line is <service letter><field letter>=<value>. Services a=auth b=billing s=search "
          "c=cache g=gateway. Fields r=replicas t=timeout_ms y=retries o=owner g=region l=log_level m=max_conn "
          "e=tier. Example: at=700 is auth.timeout_ms = 700; gg=ap-south is gateway.region = ap-south. "
          "Operations may use codes or full keys.")
KEYRX = re.compile(r"^[a-z]+\.[a-z_]+$")


def key_of(tok):
    t = tok.strip("`'\",;")
    if KEYRX.match(t):
        return t
    if t in KEY:
        return KEY[t]
    raise OpError(f"unknown key '{tok}'")


def val_of(tok):
    v = tok.strip("`'\",;")
    return REGI.get(v, v)


def num(state, k):
    if k not in state:
        raise OpError(f"{k} does not exist")
    try:
        return int(state[k])
    except ValueError:
        raise OpError(f"{k} is not a number")


OPS = {"SET", "DEL", "INHERIT", "FUSE", "SCALE", "ROUTE", "REHOST"}
FLD_LETTER = {"r": "replicas", "t": "timeout_ms", "y": "retries", "o": "owner", "g": "region", "l": "log_level",
              "m": "max_conn", "e": "tier"}
SKIPPED = []                                               # prose lines skipped by the parser (all arms)
ROUTE_RX = re.compile(r"^ROUTE\s+(\S+)\s*=\s*(\S+)\s*:\s*(\S+)\s+(\S+)\s*\|\s*(\S+)$")


def parse_ops(text, after_sep=False):
    lines = text.strip().split("\n")
    if after_sep:
        if "---" not in [x.strip() for x in lines]:
            raise OpError("no '---' line before the operations")
        lines = lines[[x.strip() for x in lines].index("---") + 1:]
    ops = []
    for raw in lines:
        s = raw.strip()
        s = re.sub(r"^(?:[-*]\s+|\d+[.)]\s+)", "", s).strip()
        if not s or s.startswith("```"):
            continue
        s = re.sub(r"^(SET\s+\S+?)\s*=\s*(\S+)$", r"\1 \2", s)          # SET k=v, SET k = v
        w = s.split()
        kw = w[0].upper()
        if kw not in OPS:                                  # prose line: skipped, counted
            SKIPPED.append(s)
            continue
        if kw == "ROUTE":
            m = ROUTE_RX.match("ROUTE " + s.split(None, 1)[1] if len(w) > 1 else s)
            if not m:
                raise OpError(f"cannot parse '{s}'")
            ops.append(("ROUTE", key_of(m.group(1)), val_of(m.group(2)), key_of(m.group(3)), val_of(m.group(4)),
                        val_of(m.group(5))))
            continue
        cap = None
        if "CAP" in [x.upper() for x in w]:
            i = [x.upper() for x in w].index("CAP")
            if i + 1 >= len(w):
                raise OpError(f"CAP without a value in '{s}'")
            try:
                cap = int(w[i + 1].strip(",;"))
            except ValueError:
                raise OpError(f"bad CAP in '{s}'")
            w = w[:i] + w[i + 2:]
        if kw == "SET" and len(w) == 3:
            ops.append(("SET", key_of(w[1]), val_of(w[2])))
        elif kw == "SET" and len(w) == 4 and w[2] == "=":
            ops.append(("SET", key_of(w[1]), val_of(w[3])))
        elif kw == "DEL" and len(w) == 2:
            ops.append(("DEL", key_of(w[1])))
        elif kw == "INHERIT" and len(w) in (3, 4):
            n = 0
            if len(w) == 4:
                try:
                    n = int(w[3].replace(" ", ""))
                except ValueError:
                    raise OpError(f"bad offset in '{s}'")
            ops.append(("INHERIT", key_of(w[1]), key_of(w[2]), n, cap))
        elif kw == "FUSE" and len(w) == 4:
            ops.append(("FUSE", key_of(w[1]), key_of(w[2]), key_of(w[3]), cap))
        elif kw == "SCALE" and len(w) == 3:
            try:
                f = int(w[2])
            except ValueError:
                raise OpError(f"bad factor in '{s}'")
            ops.append(("SCALE", key_of(w[1]), f, cap))
        elif kw == "REHOST" and len(w) == 4:
            fld = w[1].strip("`'\"")
            fld = FLD_LETTER.get(fld, fld)
            if fld not in A.FORMAT:
                raise OpError(f"unknown field '{fld}'")
            ops.append(("REHOST", fld, val_of(w[2]), val_of(w[3])))
        else:
            raise OpError(f"cannot parse '{s}'")
    if not ops:
        raise OpError("no operations")
    return ops


def is_keyref(v, st):
    try:
        return key_of(v) in st and not A.valid_line(f"x.{'owner'} = {v}") and not v.isdigit()
    except OpError:
        return False


def capped(x, cap):
    return min(x, cap) if cap is not None else x


def execute(state, ops):
    """Returns (new state, source keys read). Raises OpError."""
    st = dict(state)
    srcs = []
    for op in ops:
        kw = op[0]
        if kw == "SET" and is_keyref(op[2], st):      # code fix (smoke 2): SET d s with a key = copy
            src = key_of(op[2]); srcs.append(src)
            st[op[1]] = st[src]; w = [op[1]]
        elif kw == "SET":
            st[op[1]] = op[2]; w = [op[1]]
        elif kw == "DEL":
            if op[1] not in st:
                raise OpError(f"DEL {op[1]}: no such line")
            del st[op[1]]; w = []
        elif kw == "INHERIT":
            _, d, s, n, cap = op
            if s not in st:
                raise OpError(f"INHERIT: {s} does not exist")
            srcs.append(s)
            st[d] = str(capped(num(st, s) + n, cap)) if (n or cap is not None) else st[s]; w = [d]
        elif kw == "FUSE":
            _, d, a, b, cap = op
            srcs += [a, b]
            st[d] = str(capped(num(st, a) + num(st, b), cap)); w = [d]
        elif kw == "SCALE":
            _, k, f, cap = op
            srcs.append(k)
            st[k] = str(capped(num(st, k) * f, cap)); w = [k]
        elif kw == "ROUTE":
            _, s, x, d, v1, v2 = op
            if s not in st:
                raise OpError(f"ROUTE: {s} does not exist")
            srcs.append(s)
            st[d] = v1 if st[s] == x else v2; w = [d]
        else:  # REHOST
            _, fld, a, b = op
            w = [k for k, v in st.items() if k.split(".")[1] == fld and v == a]
            srcs += w
            for k in w:
                st[k] = b
        for k in w:
            if not A.valid_line(f"{k} = {st[k]}"):
                raise OpError(f"invalid line '{k} = {st[k]}'")
    return st, list(dict.fromkeys(srcs))


def ops_text(ops):
    out = []
    for op in ops:
        kw = op[0]
        if kw == "INHERIT":
            out.append(f"INHERIT {op[1]} {op[2]}" + (f" {op[3]:+d}" if op[3] else "") +
                       (f" CAP {op[4]}" if op[4] is not None else ""))
        elif kw in ("FUSE",):
            out.append(f"FUSE {op[1]} {op[2]} {op[3]}" + (f" CAP {op[4]}" if op[4] is not None else ""))
        elif kw == "SCALE":
            out.append(f"SCALE {op[1]} {op[2]}" + (f" CAP {op[3]}" if op[3] is not None else ""))
        elif kw == "ROUTE":
            out.append(f"ROUTE {op[1]} = {op[2]} : {op[3]} {op[4]} | {op[5]}")
        else:
            out.append(" ".join(str(x) for x in op))
    return "\n".join(out)


# ---------------------------------------------------------------- palace notation (X3)

def code(k):
    return KC.get(k, k)


def pval(v):
    return v


def pline(k, v):
    return f"{code(k)}={pval(v)}"


def select_lines(req, state):
    """Generic: full key named, or service and field both named, or (non-numeric) value named as a word."""
    low = req.lower()
    words = set(re.findall(r"[a-z0-9_\-]+", low))
    out = []
    for k, v in state.items():
        s, f = k.split(".")
        if k in low or (s in words and f in words) or (not v.isdigit() and v in words):
            out.append(pline(k, v))
    return out


def changes(old, new, palace=False):
    nm = code if palace else (lambda k: k)
    out = []
    for k in old:
        if k not in new:
            out.append(f"- {nm(k)} (was {old[k]})")
        elif new[k] != old[k]:
            out.append(f"~ {nm(k)}: {old[k]} -> {new[k]}")
    for k in new:
        if k not in old:
            out.append(f"+ {nm(k)} = {new[k]}")
    return out


def before_lines(req, ops, pre, palace=False):
    """Amendment 3: the auditor sees the before-values of every line the request names (generic selection) and every
    line the operations name, so a no-change result or an 'everything owned by' transfer can be verified."""
    keys = []
    for k, v in pre.items():
        s, f = k.split(".")
        low = req.lower()
        words = set(re.findall(r"[a-z0-9_\-]+", low))
        if k in low or (s in words and f in words) or (not v.isdigit() and v in words):
            keys.append(k)
    for op in ops:
        for x in op[1:]:
            if isinstance(x, str) and x in pre:
                keys.append(x)
    keys = list(dict.fromkeys(keys))
    nm = code if palace else (lambda k: k)
    return ", ".join(f"{nm(k)}={pre[k]}" for k in keys) or "(none)"


# ---------------------------------------------------------------- prompts (static parts in the system prompt)

def planner_system(arm, set_name):
    wc = (" A request may begin with 'Worker-computed:'; treat it like any other request: the runtime computes "
          "every value from its own copy." if set_name == "S2" else "")
    if arm in ("X1", "X1s"):
        base = A.SYS["planner"]          # B1's planner prompt (S2: A4's), unchanged
        return (base + "\n\nAfter the instruction write a line containing only '---', then the RSOS operations that "
                "implement the request.\n" + GRAMMAR + wc)
    sysp = ("You are the PLANNER. Translate one change request on a configuration state into RSOS operations. Do "
            "not look up or compute any value: write the operation and let the runtime execute it. Output only "
            "the operations, nothing else.\n" + GRAMMAR + wc)
    if arm == "X3":
        sysp += "\n" + PALACE + " You see only the state lines the request names."
    return sysp


def auditor_system(arm, set_name):
    wc = (" A request beginning with 'Worker-computed:' is computed by the runtime from its own copy, which is "
          "authoritative: check the operation, its target and source, using the source values shown."
          if set_name == "S2" else "")
    s = ("You are the AUDITOR in a pipeline that edits a configuration state of lines 'service.field = value'. A "
         "planner translated a change request into RSOS operations and a deterministic runtime executed them. "
         "Check that the result implements the request exactly: every line the request changes, with the right "
         "value, and no other line. Reply with exactly 'ok', or 'no: <short reason>'.\n" + GRAMMAR + wc)
    if arm == "X3":
        s += "\n" + PALACE
    return s


def parse_audit(text):
    """Code fix (smoke 2): the auditor may reason first; the decisive line is the last one that starts with ok/no."""
    lines = [x.strip().strip("`*").strip() for x in text.strip().split("\n") if x.strip()]
    for t in reversed(lines):
        low = t.lower()
        if re.match(r"^(verdict:\s*)?ok\b", low):
            return True, ""
        if re.match(r"^(verdict:\s*)?no\b", low):
            return False, t.split(":", 1)[1].strip() if ":" in t else t
    t = text.strip()
    try:
        d = json.loads(t)
        return d.get("verdict") in ("approve", "ok"), d.get("reason", "")
    except Exception:  # noqa: BLE001
        return False, "unparseable verdict: " + t[-120:]


def audited(arm, set_name, seed, step, ops, no_change):
    if arm == "X1":
        return True
    keyset = any(op[0] == "SET" and (KEYRX.match(op[2]) or op[2] in KEY) for op in ops)   # SET d s = copy
    if no_change or keyset or any(op[0] in RISK_OPS for op in ops):
        return True
    return int(hashlib.sha256(f"{set_name}:{seed}:{step}".encode()).hexdigest(), 16) % 4 == 0


# ---------------------------------------------------------------- the X loop

def run_x(arm, set_name, seed, tag=None, planner=None, auditor=None):
    """planner/auditor: optional fakes (replay check oracle); default is the live model call."""
    task = A.make_task(seed)
    truths = task["truths"]
    plan = A.drift_plan(task, truths)
    psys, asys = planner_system(arm, set_name), auditor_system(arm, set_name)
    log, msgs, calls, drift_events, step_log = [], [], [], [], []
    t_start = time.time()
    ctx = {"step": 0, "attempt": 0}

    def send(a, b, text, kind="msg"):
        msgs.append({"step": ctx["step"], "attempt": ctx["attempt"], "from": a, "to": b, "text": text,
                     "tok": A.ntok(text), "bpe": H.bpe(text), "bytes": len(text.encode()), "kind": kind})

    def call(role, system, prompt):
        fake = planner if role == "planner" else auditor
        if fake is not None:
            text, rec = fake(prompt, ctx), {"in": 0, "cache_w": 0, "cache_w5m": 0, "cache_w1h": 0, "cache_r": 0,
                                            "out": 0, "think": 0, "sec": 0.0, "cost": 0.0}
        else:
            text, _, rec = L.llm(system, prompt, None, log)
        rec = {**rec, "role": role, "step": ctx["step"], "attempt": ctx["attempt"]}
        calls.append(rec)
        return text

    copies = {r: A.text_of(task["init"]) for r in ("planner", "worker", "checker")}
    snap = copies["planner"]
    step_fail = invalid_ops = 0
    for st, req in enumerate(task["requests"]):
        ctx["step"], ctx["attempt"] = st, 0
        dr = plan.get(st)
        d_ev = None
        if dr:                                            # same drift as B1: the worker copy
            ws = A.state_of_text(copies["worker"]); ws[dr[0]] = dr[1]; copies["worker"] = A.text_of(ws)
            d_ev = {"step": st, "key": dr[0], "true": truths[st][dr[0]], "wrong": dr[1]}
        t0 = time.time()
        for r in copies:                                  # green dot vs the agreed snapshot; heal by reference
            if PAL.h(copies[r]) != PAL.h(snap):
                w, s = copies[r].split("\n"), snap.split("\n")
                idx = [i for i in range(min(len(w), len(s))) if w[i] != s[i]]
                copies[r] = snap
                send(r, "runtime", "!" + ",".join(map(str, idx)), kind="heal")
                if d_ev and r == "worker":
                    d_ev.update({"detected_by": "snapshot_sha", "recovery_tok": A.ntok("!" + ",".join(map(str, idx))),
                                 "recovery_sec": time.time() - t0})
        if d_ev:
            d_ev["pre_worker_true"] = A.state_of_text(copies["worker"]).get(d_ev["key"]) == d_ev["true"]
        pre = A.state_of_text(snap)
        feedback, ok = "", False
        srec = {"step": st, "attempts": []}
        for attempt in range(A.MAX_RETRY + 1):
            ctx["attempt"] = attempt
            if arm == "X3":
                sel = select_lines(req, pre)
                body = f"Change request: {req}\n\nLines:\n" + ("\n".join(sel) if sel else "(none named)")
            else:
                body = f"Change request: {req}\n\nState:\n{snap}"
            ptext = call("planner", psys, body + feedback)
            arec = {"planner_out": ptext}
            try:
                ops = parse_ops(ptext, after_sep=arm in ("X1", "X1s"))
                outs = [execute(A.state_of_text(copies[r]), ops) for r in copies]
                if any(o[0] != outs[0][0] for o in outs):
                    raise OpError("copies disagree after execution")
                new, srcs = outs[0]
            except OpError as e:
                invalid_ops += 1
                arec["invalid"] = str(e)
                send("runtime", "planner", f"invalid: {e}", kind="invalid")
                feedback = f"\n\nThe runtime rejected your previous output: {e}\nPrevious output:\n{ptext.strip()}"
                srec["attempts"].append(arec)
                continue
            otext = ops_text(ops)
            send("planner", "runtime", otext)
            arec["ops"] = otext
            ch = changes(pre, new, palace=(arm == "X3"))
            need = audited(arm, set_name, seed, st, ops, not ch)
            arec["audited"] = need
            good, reason = True, ""
            if need:
                nm = code if arm == "X3" else (lambda k: k)
                src_txt = ", ".join(f"{nm(k)}={pre[k]}" for k in srcs if k in pre) or "(none)"
                named = before_lines(req, ops, pre, palace=(arm == "X3"))      # amendment 3
                ap = (f"Change request: {req}\n\nOperations:\n{otext}\n\nResult (executed by the runtime):\n" +
                      ("\n".join(ch) if ch else "(no change)") + f"\nSource values read: {src_txt}" +
                      f"\nLines the request or the operations name, before the change: {named}")
                send("runtime", "auditor", ap.split("\n\n", 2)[-1])
                atext = call("auditor", asys, ap)
                good, reason = parse_audit(atext)
                send("auditor", "runtime", "ok" if good else "no: " + reason)
                arec["audit"] = atext.strip()[-1500:]
            arec["approved"] = good
            srec["attempts"].append(arec)
            if good:
                ntext = A.text_of(new)
                for r in copies:
                    copies[r] = ntext
                assert len({PAL.h(c) for c in copies.values()}) == 1
                snap = ntext
                ok = True
                break
            feedback = (f"\n\nThe auditor rejected your previous operations: {reason}\nPrevious operations:\n{otext}")
        # step truth transition (analysis only)
        expect = dict(pre)
        for k in set(truths[st]) | set(truths[st + 1]):
            if k not in truths[st + 1]:
                expect.pop(k, None)
            elif truths[st].get(k) != truths[st + 1][k]:
                expect[k] = truths[st + 1][k]
        got = A.state_of_text(snap)
        srec.update({"ok": ok, "correct": got == expect})
        last = srec["attempts"][-1] if srec["attempts"] else {}
        if ok and got != expect:
            srec["audit_miss"] = "approved" if last.get("audited") else "unsampled"
        step_log.append(srec)
        if not ok:
            step_fail += 1
        if d_ev:
            cs = [A.state_of_text(c) for c in copies.values()]
            d_ev["healed"] = all(c.get(d_ev["key"]) == d_ev["true"] for c in cs)
            d_ev["healed_zero_call"] = d_ev["healed"] and d_ev["pre_worker_true"]
            d_ev["caught"] = A.state_of_text(copies["planner"]).get(d_ev["key"]) == d_ev["true"]
            d_ev.setdefault("detected_by", "none")
            drift_events.append(d_ev)
    final = A.state_of_text(copies["planner"])
    cs = [A.state_of_text(c) for c in copies.values()]
    truth = task["final"]
    keys = set(truth) | set(final)
    acc = sum(final.get(k) == truth.get(k) for k in keys) / len(keys)
    for e in drift_events:
        e["silent_in_final"] = final.get(e["key"]) != e["true"]
        e["in_any_copy_final"] = any(c.get(e["key"]) != e["true"] for c in cs)
    success = final == truth
    res = {"arm": arm, "cond": arm, "seed": seed, "tag": tag, "success": success, "line_acc": acc,
           "replica_success": all(dict.__eq__(truth, c) if isinstance(truth, dict) else c == truth for c in cs),
           "final_errors": sorted(k for k in keys if final.get(k) != truth.get(k)), "final_state": final,
           "steps_failed": step_fail, "invalid_ops": invalid_ops, "n_msgs": len(msgs), "n_calls": len(calls),
           "channel_tok": sum(m["tok"] for m in msgs), "channel_bpe": sum(m["bpe"] for m in msgs),
           "channel_bytes": sum(m["bytes"] for m in msgs),
           "billed_tok": sum(A.billed(c) for c in calls), "out_tok": sum(c["out"] for c in calls),
           "in_tok": sum(c["in"] + c["cache_w"] + c["cache_r"] for c in calls),
           "cost_usd": sum(c["cost"] or 0 for c in calls), "wall_sec": time.time() - t_start,
           "drift": drift_events, "steps": step_log, "calls_full": calls,
           "per_msg": [{k: m[k] for k in ("step", "attempt", "from", "to", "tok", "bpe", "bytes", "kind")}
                       for m in msgs]}
    tr = os.environ.get("A5_TRANSCRIPTS")
    if tr:
        with _wlock:
            with open(tr, "a") as f:
                f.write(json.dumps({"arm": arm, "set": set_name, "seed": seed, "tag": tag, "msgs": msgs,
                                    "calls": log, "steps": step_log}) + "\n")
    print(f"{set_name} {arm} {seed} success={success} acc={acc:.3f} calls={len(calls)} out={res['out_tok']} "
          f"inv={invalid_ops} fail={step_fail} wall={res['wall_sec']:.0f}s", flush=True)
    return res, task


# ---------------------------------------------------------------- X5 (amendment 2): the assembly line

X5_PLAN = (" You receive all change requests of one task, numbered; the runtime applies them in order. For each "
           "request write a line '#<number>' and then its operations.")
X5_AUDIT = (" You receive numbered steps, each executed on the result of the previous one. Reply with one line per "
            "step: '<number> ok' or '<number> no: <short reason>'.")


def split_steps(text, n):
    """'#k' headers -> {k: ops text}."""
    out, cur = {}, None
    for line in text.split("\n"):
        m = re.match(r"^\s*#\s*(\d+)\s*:?\s*(.*)$", line)
        if m and 0 <= int(m.group(1)) < n + 1:
            cur = int(m.group(1)); out[cur] = []
            if m.group(2).strip():
                out[cur].append(m.group(2))
        elif cur is not None:
            out[cur].append(line)
    return {k: "\n".join(v) for k, v in out.items()}


def parse_verdicts(text):
    out = {}
    for line in text.split("\n"):
        m = re.match(r"^\s*#?\s*(\d+)\s*[:.)-]?\s*(ok|no)\b\s*:?\s*(.*)$", line.strip(), re.I)
        if m:
            out[int(m.group(1))] = (m.group(2).lower() == "ok", m.group(3).strip())
    return out


def simulate(task, plan, ops_by_step, send=None):
    """Execute the whole task: drift injection and heal before every step, then the step's operations (None =
    step left out). Returns per-step records and drift events. Deterministic, 0 model calls."""
    truths = task["truths"]
    copies = {r: A.text_of(task["init"]) for r in ("planner", "worker", "checker")}
    snap = copies["planner"]
    steps, drift = [], []
    for st in range(len(task["requests"])):
        dr = plan.get(st)
        d_ev = None
        if dr:
            ws = A.state_of_text(copies["worker"]); ws[dr[0]] = dr[1]; copies["worker"] = A.text_of(ws)
            d_ev = {"step": st, "key": dr[0], "true": truths[st][dr[0]], "wrong": dr[1]}
        for r in copies:
            if PAL.h(copies[r]) != PAL.h(snap):
                w, s = copies[r].split("\n"), snap.split("\n")
                idx = [i for i in range(min(len(w), len(s))) if w[i] != s[i]]
                copies[r] = snap
                if send:
                    send(st, r, "runtime", "!" + ",".join(map(str, idx)), "heal")
                if d_ev and r == "worker":
                    d_ev.update({"detected_by": "snapshot_sha", "recovery_tok": A.ntok("!" + ",".join(map(str, idx)))})
        if d_ev:
            d_ev["pre_worker_true"] = A.state_of_text(copies["worker"]).get(d_ev["key"]) == d_ev["true"]
        pre = A.state_of_text(snap)
        rec = {"step": st, "pre": pre, "new": pre, "srcs": [], "error": None}
        ops = ops_by_step.get(st)
        if ops is not None:
            try:
                outs = [execute(A.state_of_text(copies[r]), ops) for r in copies]
                if any(o[0] != outs[0][0] for o in outs):
                    raise OpError("copies disagree after execution")
                rec["new"], rec["srcs"] = outs[0]
                ntext = A.text_of(rec["new"])
                for r in copies:
                    copies[r] = ntext
                snap = ntext
            except OpError as e:
                rec["error"] = str(e)
        steps.append(rec)
        if d_ev:
            cs = [A.state_of_text(c) for c in copies.values()]
            d_ev["healed"] = all(c.get(d_ev["key"]) == d_ev["true"] for c in cs)
            d_ev["healed_zero_call"] = d_ev["healed"] and d_ev["pre_worker_true"]
            d_ev["caught"] = A.state_of_text(copies["planner"]).get(d_ev["key"]) == d_ev["true"]
            d_ev.setdefault("detected_by", "none")
            drift.append(d_ev)
    return steps, drift, copies


def run_x5(set_name, seed, tag=None, planner=None, auditor=None):
    arm = "X5"
    task = A.make_task(seed)
    truths = task["truths"]
    plan = A.drift_plan(task, truths)
    n = len(task["requests"])
    psys = planner_system("X3", set_name) + X5_PLAN
    asys = auditor_system("X3", set_name) + X5_AUDIT
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
    ops_by = {}                    # step -> ops (current plan)
    ops_txt = {}
    approved = set()
    feedback = {}                  # step -> reason
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
            sel = select_lines(task["requests"][k], init)
            block = f"#{k + 1} {task['requests'][k]}"
            if sel:
                block += "\nLines: " + " ".join(sel)
            if k in feedback:
                block += f"\nRejected before: {feedback[k]}\nPrevious operations: {ops_txt.get(k, '(invalid)')}"
            lines.append(block)
        ptext = call("planner", psys, "Change requests:\n" + "\n\n".join(lines))
        parts = split_steps(ptext, n)
        for k in todo:
            attempts[k] += 1
            body = parts.get(k + 1)
            try:
                if body is None:
                    raise OpError("no operations for this step")
                ops_by[k] = parse_ops(body)
                ops_txt[k] = ops_text(ops_by[k])
                send(k, "planner", "runtime", f"#{k + 1}\n" + ops_txt[k])
            except OpError as e:
                invalid_ops += 1
                ops_by.pop(k, None); ops_txt.pop(k, None)
                feedback[k] = f"the runtime rejected the output: {e}"
                send(k, "runtime", "planner", f"#{k + 1} invalid: {e}", kind="invalid")
        steps, _, _ = simulate(task, plan, {k: v for k, v in ops_by.items()})
        for k in todo:                               # execution errors on the actual pre-state
            if k in ops_by and steps[k]["error"]:
                invalid_ops += 1
                feedback[k] = f"the runtime rejected the operations: {steps[k]['error']}"
                send(k, "runtime", "planner", f"#{k + 1} invalid: {steps[k]['error']}", kind="invalid")
                ops_by.pop(k)
        steps, _, _ = simulate(task, plan, {k: v for k, v in ops_by.items()})
        cand = [k for k in todo if k in ops_by]
        sel_audit = [k for k in cand if audited("X5", set_name, seed, k, ops_by[k],
                                                 not changes(steps[k]["pre"], steps[k]["new"]))]
        for k in cand:
            if k not in sel_audit:
                approved.add(k)
        if sel_audit:
            blocks = []
            for k in sel_audit:
                s = steps[k]
                ch = changes(s["pre"], s["new"], palace=True)
                src = ", ".join(f"{code(x)}={s['pre'][x]}" for x in s["srcs"] if x in s["pre"]) or "(none)"
                blocks.append(f"#{k + 1} {task['requests'][k]}\nOps: " + ops_txt[k].replace("\n", " ; ") +
                              "\nResult: " + ("; ".join(ch) if ch else "(no change)") + f"\nSources: {src}" +
                              "\nBefore: " + before_lines(task["requests"][k], ops_by[k], s["pre"], palace=True))
            ap = "Steps:\n" + "\n\n".join(blocks)
            send(-1, "runtime", "auditor", ap)
            atext = call("auditor", asys, ap)
            ver = parse_verdicts(atext)
            if not any(k + 1 in ver for k in sel_audit) and len(ver) == len(sel_audit) and \
                    sorted(ver) == list(range(1, len(sel_audit) + 1)):          # code fix: numbered by position
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
    steps, drift_events, copies = simulate(task, plan, final_ops, send=lambda st, a, b, t, kd: send(st, a, b, t, kd))
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
               "ops": ops_txt.get(st) if ok else None,
               "audited": ok and audited("X5", set_name, seed, st, final_ops[st],
                                         not changes(steps[st]["pre"], steps[st]["new"]))}
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
    res = {"arm": arm, "cond": arm, "seed": seed, "tag": tag, "success": success, "line_acc": acc,
           "replica_success": all(dict.__eq__(truth, c) for c in cs),
           "final_errors": sorted(k for k in keys if final.get(k) != truth.get(k)), "final_state": final,
           "steps_failed": sum(1 for s in step_log if not s["ok"]), "invalid_ops": invalid_ops,
           "n_msgs": len(msgs), "n_calls": len(calls),
           "channel_tok": sum(m["tok"] for m in msgs), "channel_bpe": sum(m["bpe"] for m in msgs),
           "channel_bytes": sum(m["bytes"] for m in msgs),
           "billed_tok": sum(A.billed(c) for c in calls), "out_tok": sum(c["out"] for c in calls),
           "in_tok": sum(c["in"] + c["cache_w"] + c["cache_r"] for c in calls),
           "cost_usd": sum(c["cost"] or 0 for c in calls), "wall_sec": time.time() - t_start,
           "drift": drift_events, "steps": step_log, "audits": audit_log, "calls_full": calls,
           "per_msg": [{k: m[k] for k in ("step", "attempt", "from", "to", "tok", "bpe", "bytes", "kind")}
                       for m in msgs]}
    tr = os.environ.get("A5_TRANSCRIPTS")
    if tr:
        with _wlock:
            with open(tr, "a") as f:
                f.write(json.dumps({"arm": arm, "set": set_name, "seed": seed, "tag": tag, "msgs": msgs,
                                    "calls": log, "steps": step_log}) + "\n")
    print(f"{set_name} {arm} {seed} success={success} acc={acc:.3f} calls={len(calls)} out={res['out_tok']} "
          f"inv={invalid_ops} fail={res['steps_failed']} wall={res['wall_sec']:.0f}s", flush=True)
    return res, task
