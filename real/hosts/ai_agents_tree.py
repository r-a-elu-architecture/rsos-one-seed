"""REAL1 row 1 "ai_agents": THE REAL TREE (owner, 24 Nov: the seed's own future is read from the real tree, not from new
paid calls and not from one sample).

Reads the recorded runs of real models (layer-1 records, nothing simulated):
  experiments/agents/phase3_staff.jsonl, phase3_orders.jsonl   sealed phase 3 (design v3), 4 models, arms
                                                                react / selfcons / reflexion / planexec / rsos_01100,
                                                                seeds staff 5000-5149, orders 3000-3149
  experiments/agents/quick2_*.jsonl, quick3_*.jsonl            design v3 + provider pinning, arms react / react_b (plain
                                                                ReAct) / rsos2 / rsos3, seeds 6000-6029, 6100-6129, 4000-4029,
                                                                4100-4129
No record comes from the test cells (those use task seeds 7,000,000+). Only plain ReAct attempts are used (arms react,
react_b: one attempt at temperature 0; arm selfcons: up to 3 attempts at temperature 0.7 in one shared budget); reflexion,
planexec and the rsos arms run other loops (verification calls, plans) and are not attempts of the host's branches.

An ATTEMPT is split out of a record's trace at every call whose input starts with "Task:" (validated: on 2,400 phase-3
react/selfcons records the trace length equals the recorded call count in every record, and the majority of the parsed
attempt answers equals the recorded selfcons answer in all but one). Each call of an attempt is a STATE of the tree:
  k    calls already made in this attempt (0 = before its first call)
  e    0/1: an error observation or a format note has occurred in this attempt so far
  prev outcomes of the earlier attempts on the same task (answered right c, answered wrong w; clipped at 2), two variants:
       w..  within the record (self-consistency attempts after earlier self-consistency attempts)
       p..  paired: a self-consistency attempt 0 conditioned on the ReAct arm's outcome on the same model and task
            (phase 3 is paired); this is the record of "a temperature-0.7 attempt next to a temperature-0 ReAct attempt"
The CONTINUATION of a state is what really followed: r = further calls until the attempt's ANSWER (that call included), or
"x" = no answer before the shared budget ran out, and ok = the answer was right (tasks.correct against the record's exact
answer).

OUTPUT real/hosts/data/ai_agents_tree.json (deterministic: sorted keys, no time stamps; sha256 of each source recorded):
  cont[key]     key "model|family|temp|k|e|prev" (prev "-" = all prevs pooled): {"n", "r": {r: [n, n_ok]}, "tok_rem"}
                P(final answer right | state) = sum n_ok / n; tok_rem = expected remaining tokens of this attempt (per-call
                tokens from the fit below, attempt-local context)
  ans[key]      key "model|family|temp|c|e|prev": [n_ok, n] for attempts that ANSWERED at their call c (e at that time):
                how often an answer given in that state was right
  restart[key]  key "model|family|k|e": continuations of the paired self-consistency attempt 0 (fresh context,
                temperature 0.7) on the tasks where the ReAct attempt was still unanswered after k calls with error state e:
                the real record of "abandon the stuck ReAct context and start afresh" on exactly those tasks; "pair" =
                discordant pairs on those same tasks [restart right & ReAct wrong, ReAct right & restart wrong]
  collide[key]  key "model|family": [n_same, n]: a wrong answer equals an earlier wrong answer of the same task
  tok[key]      key "model|family": per-call tokens of ReAct, least squares on the react records:
                tokens_task = a * calls + g * calls * (calls - 1) / 2  (a = first call, g = growth per call)
  model and family may be "*" (pooled), for back-off when a cell of the tree is thin.
Usage: python real/hosts/ai_agents_tree.py   (writes the json and prints a summary)"""
import os, sys, json, math, hashlib, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
AG = os.path.join(ROOT, "experiments", "agents")
if AG not in sys.path: sys.path.insert(0, AG)
from agent import last_line, ACT, ANS          # noqa: E402  (the harness's own parsers)
from tasks import correct                       # noqa: E402

SOURCES = ["phase3_staff.jsonl", "phase3_orders.jsonl", "quick2_staff.jsonl", "quick2_orders.jsonl",
           "quick3_staff.jsonl", "quick3_orders.jsonl"]
OUT = os.path.join(HERE, "data", "ai_agents_tree.json")
T_ARMS = {"react": "0", "react_b": "0", "selfcons": "0.7"}


def norm(a): return str(a).strip().rstrip(".")


def attempts(rec):
    """Split a record's trace into attempts: [(calls list, answer or None, ok, [e after each call])]."""
    atts = []
    for t in rec["trace"]:
        if t["in"].startswith("Task:") or not atts: atts.append([])
        atts[-1].append(t)
    out = []
    for calls in atts:
        e = 0; es = []; ans = None
        for i, t in enumerate(calls):
            if i > 0 and (t["in"].startswith("Observation: error") or t["in"].startswith("Reply must end")): e = 1
            es.append(e)                                  # e known BEFORE call i (observations reach the call's input)
        o = calls[-1]["out"]; m = last_line(o, ANS)
        if m and not last_line(o, ACT): ans = norm(m.group(1))
        out.append((calls, ans, bool(ans is not None and correct({"answer": rec["answer"]}, ans)), es))
    return out


def tag(nc, nw, v): return f"{v}c{min(nc, 2)}w{min(nw, 2)}"


def build():
    recs = []; sha = {}
    for fn in SOURCES:
        p = os.path.join(AG, fn); raw = open(p, "rb").read(); sha[fn] = hashlib.sha256(raw).hexdigest()
        for line in raw.decode().splitlines():
            r = json.loads(line)
            if r["arm"] in T_ARMS: recs.append(r)
    cont = collections.defaultdict(lambda: {"n": 0, "r": collections.defaultdict(lambda: [0, 0]), "tok": 0.0})
    ans = collections.defaultdict(lambda: [0, 0])
    restart = collections.defaultdict(lambda: {"n": 0, "r": collections.defaultdict(lambda: [0, 0]), "pair": [0, 0]})
    coll = collections.defaultdict(lambda: [0, 0])
    # token fit per (model, family) on ReAct records: normal equations for tokens = a*c + g*c(c-1)/2
    S = collections.defaultdict(lambda: [0.0] * 5)
    for r in recs:
        if T_ARMS[r["arm"]] != "0" or not r["calls"]: continue
        c = r["calls"]; x1, x2 = c, c * (c - 1) / 2
        for key in (f"{r['model']}|{r['family']}", f"*|{r['family']}", f"{r['model']}|*", "*|*"):
            s = S[key]; s[0] += x1 * x1; s[1] += x1 * x2; s[2] += x2 * x2; s[3] += x1 * r["tokens"]; s[4] += x2 * r["tokens"]
    tok = {}
    for key, (a11, a12, a22, b1, b2) in S.items():
        det = a11 * a22 - a12 * a12
        a = (b1 * a22 - b2 * a12) / det; g = (a11 * b2 - a12 * b1) / det
        tok[key] = {"a": round(a, 1), "g": round(g, 1)}

    def per_call(model, fam, i):
        t = tok.get(f"{model}|{fam}") or tok["*|*"]; return t["a"] + t["g"] * i

    # paired ReAct outcome per (model, task): prev for self-consistency attempt 0 (variant p); ReAct states for restart
    react_of = {}
    for r in recs:
        if r["arm"] == "react" and r["task"][1:].isdigit() and r["trace"]:
            react_of[(r["model"], r["task"])] = attempts(r)[0]
    for r in recs:
        temp = T_ARMS[r["arm"]]; m, f = r["model"], r["family"]; atts = attempts(r)
        nc = nw = 0; wrong_seen = []
        for ai, (calls, a, ok, es) in enumerate(atts):
            n = len(calls); prevs = ["-", tag(nc, nw, "w")]
            if temp == "0.7" and ai == 0 and (m, r["task"]) in react_of:
                _, ra, rok, _ = react_of[(m, r["task"])]
                prevs.append(tag(int(ra is not None and rok), int(ra is not None and not rok), "p"))
            for k in range(n):
                rr = str(n - k) if a is not None else "x"
                rem = sum(per_call(m, f, i) for i in range(k, n))
                for pv in prevs:
                    for mm in (m, "*"):
                        for ff in (f, "*"):
                            node = cont[f"{mm}|{ff}|{temp}|{k}|{es[k]}|{pv}"]
                            node["n"] += 1; node["r"][rr][0] += 1; node["r"][rr][1] += int(ok); node["tok"] += rem
            if a is not None:
                e_ans = es[n - 1]
                for pv in prevs:
                    for mm in (m, "*"):
                        for ff in (f, "*"):
                            x = ans[f"{mm}|{ff}|{temp}|{n}|{e_ans}|{pv}"]; x[0] += int(ok); x[1] += 1
                if not ok:
                    if wrong_seen:
                        for mm in (m, "*"):
                            for ff in (f, "*"):
                                c = coll[f"{mm}|{ff}"]; c[0] += int(a in wrong_seen); c[1] += 1
                    wrong_seen.append(a)
                nc += int(ok); nw += int(not ok)
        # restart: the ReAct attempt's unanswered states on this task -> this task's self-consistency attempt 0
        if temp == "0.7" and atts and (m, r["task"]) in react_of:
            rcalls, ra, rok, res = react_of[(m, r["task"])]; calls0, a0, ok0, _ = atts[0]
            rr = str(len(calls0)) if a0 is not None else "x"
            last_unans = len(rcalls) - (1 if ra is not None else 0)     # states k = 1..last_unans are "still unanswered"
            for k in range(1, last_unans + 1):
                e = res[k] if k < len(res) else res[-1]
                for mm in (m, "*"):
                    for ff in (f, "*"):
                        node = restart[f"{mm}|{ff}|{k}|{e}"]; node["n"] += 1; node["r"][rr][0] += 1; node["r"][rr][1] += int(ok0)
                        node["pair"][0] += int(ok0 and not rok); node["pair"][1] += int(rok and not ok0)
    out = {"meta": {"sources": sha, "records_used": len(recs), "arms": T_ARMS,
                    "note": "recorded real runs only; task seeds staff 5000-5149, 6000-6029, 6100-6129; orders 3000-3149, "
                            "4000-4029, 4100-4129; the test cells use 7,000,000+"},
           "tok": tok,
           "cont": {k: {"n": v["n"], "r": {rr: list(x) for rr, x in sorted(v["r"].items())},
                        "tok_rem": round(v["tok"] / v["n"], 1)} for k, v in sorted(cont.items())},
           "ans": {k: list(v) for k, v in sorted(ans.items())},
           "restart": {k: {"n": v["n"], "r": {rr: list(x) for rr, x in sorted(v["r"].items())}, "pair": v["pair"]}
                       for k, v in sorted(restart.items())},
           "collide": {k: list(v) for k, v in sorted(coll.items())}}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh: json.dump(out, fh, sort_keys=True, separators=(",", ":"))
    return out


def sign_p(n_better, n_worse):
    """One-sided exact sign test on the discordant pairs: P(X >= n_better | n_better + n_worse, 1/2)."""
    n = n_better + n_worse
    return sum(math.comb(n, i) for i in range(n_better, n + 1)) / 2 ** n if n else 1.0


def p_ok(node): return sum(x[1] for x in node["r"].values()) / node["n"]


if __name__ == "__main__":
    t = build(); raw = open(OUT, "rb").read()
    print(f"wrote {OUT}  ({len(raw)} bytes, sha256 {hashlib.sha256(raw).hexdigest()[:16]})")
    print(f"records used {t['meta']['records_used']}; nodes: cont {len(t['cont'])}, ans {len(t['ans'])}, "
          f"restart {len(t['restart'])}, collide {len(t['collide'])}")
    M = "openrouter:openai/gpt-oss-20b"
    for f in ("staff", "orders"):
        print(f"\n{M} {f}: tokens per call a={t['tok'][f'{M}|{f}']['a']} g={t['tok'][f'{M}|{f}']['g']}; "
              f"wrong-answer collisions {t['collide'].get(f'{M}|{f}')}")
        print("  k e | ReAct T0 continue: n  P(ok)  tok_rem | restart (fresh T0.7): n  P(ok)")
        for k in range(0, 9):
            for e in (0, 1):
                c = t["cont"].get(f"{M}|{f}|0|{k}|{e}|-"); rs = t["restart"].get(f"{M}|{f}|{k}|{e}")
                if not c: continue
                rtxt = (f"{rs['n']:4d}  {p_ok(rs):.3f}  paired restart-better/react-better {rs['pair'][0]}/{rs['pair'][1]}"
                        f"  p={sign_p(*rs['pair']):.3f}") if rs else "   -     -"
                print(f"  {k} {e} | {c['n']:4d}  {p_ok(c):.3f}  {c['tok_rem']:7.0f} | {rtxt}")
        print("  self-consistency attempt by prev (k=0): " + ", ".join(
            f"{pv} n={t['cont'][f'{M}|{f}|0.7|0|0|{pv}']['n']} P={p_ok(t['cont'][f'{M}|{f}|0.7|0|0|{pv}']):.2f}"
            for pv in ("wc0w0", "wc1w0", "wc0w1", "wc2w0", "wc1w1", "wc0w2", "pc1w0", "pc0w1", "pc0w0")
            if f"{M}|{f}|0.7|0|0|{pv}" in t["cont"]))
