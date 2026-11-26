"""REAL3 row 1 "ai_agents": the BLIND PLANNING runtime, HOLOGRAM CONTEXT and the O-trace PLAN POOL (frame levers).

BLIND PLANNING (the loop of experiments/a7_arms.py run_plan arm X5b, sealed A7/A8, carried to the tool-use tasks):
  the model writes the PLAN of operations ONCE, over key names and references (#k), and never sees a data value; this
  runtime calls the task's real tools (tasks.run_tool, the same tools ReAct uses), computes every value and returns the
  answer. The runtime checks the plan (parse, references, tool errors, an empty selection, a non-scalar answer); the model
  is called again ONLY on a detected failure, with its previous operations and the runtime's reason (A7: "Rejected before:
  <reason> / Previous operations: <ops>"), at most MAX_RETRY = 2 re-plans (a1_agents.MAX_RETRY, the A7 value).
HOLOGRAM CONTEXT: a re-plan call carries the question, the previous plan, the failure and a DIGEST of the run (per line:
  kind and size: "3 keys", "5 records (fields ...)", "number"), never the transcript and never a value.
PLAN POOL (O-trace across tasks of the same type): a plan that executed and whose answer was the committed answer of its
  task is stored under its SHAPE: the question with the plan's literals (the values the plan names that occur in the
  question as words) replaced by slots. A later question of the same shape binds the slots and runs the plan with zero
  model calls. The pool is process-wide (like seed3.POOL: shared across cells and standards, keyed by model spec and
  family); an entry whose answers are contradicted at commit more often than confirmed is removed. No ground truth.

Grammar (one operation per line, '#k op(args)'; last line 'ANSWER #k'):
  tool calls        filter(dept=Sales), lookup(#1), orders_where(product=lamp), order_details(#1)   (a #k argument = its keys;
                    order_details is batched by 10 by the runtime)
  and(#a, #b) or(#a, #b)          keys in both / either
  where(#k, field OP value)       records of #k with field OP value (OP = != > >= < <=); key lists are fetched first
  sum avg min max (#k, expr)      expr = field or fields joined by * (qty*price)
  count(#k)  argmax argmin(#k[, expr])  (ties: first alphabetically)   group(#k, field, expr)  calc(expr with #refs)  floor(#k)
"""
import re, json, math, collections
import numpy as np
from tasks import run_tool, calc, TOOL_HELP, NAMES

MAX_RETRY = 2
OPN = ("and", "or", "where", "sum", "avg", "min", "max", "count", "argmax", "argmin", "group", "calc", "floor")
CMP = {"=": lambda a, b: a == b, "!=": lambda a, b: a != b, ">": lambda a, b: a > b, ">=": lambda a, b: a >= b,
       "<": lambda a, b: a < b, "<=": lambda a, b: a <= b}
LINE = re.compile(r"^\s*#\s*(\d+)\s*[:.)]?\s*(\w+)\s*\((.*)\)\s*$")
ANSL = re.compile(r"^\s*ANSWER\s*:?\s*#\s*(\d+)\s*$", re.I)
WHERE = re.compile(r"^\s*(\w+)\s*(!=|>=|<=|=|>|<)\s*['\"]?(.+?)['\"]?\s*$")
EXEC = {}                 # O-trace (spec, family) -> [plan calls that executed, plan calls]
TRACE = {}                # O-trace (spec, family, "plan" | "replan") -> [tokens, calls]
PLAN_POOL = {}            # (spec, family, shape) -> {"plan", "rx", "uses", "exec_ok", "agree", "disagree"}


class PlanError(Exception):
    pass


def system_prompt(task):
    tools = "\n".join("- " + TOOL_HELP[t] for t in task["tools"] if t != "calc")
    return ("You write a PLAN of operations for a runtime. You see no data values: the runtime calls the tools, reads "
            "every record and computes every value. One operation per line, numbered '#1 ...', '#2 ...'; an argument "
            "#k refers to the result of line k. Last line: ANSWER #k\nTool operations (an argument may be #k = its keys):\n"
            + tools + "\nRuntime operations:\n- and(#a, #b) / or(#a, #b): keys in both / in either\n"
            "- where(#k, field OP value): the records of #k whose field compares (OP is = != > >= < <=)\n"
            "- sum(#k, expr) / avg / min / max: expr is a field or fields joined by * (e.g. qty*price)\n- count(#k)\n"
            "- argmax(#k, expr) / argmin: the key with the largest / smallest value (ties: first alphabetically)\n"
            "- group(#k, field, expr): per value of field, the sum of expr (argmax(#k) then gives the top group)\n"
            "- calc(expression with numbers and #refs), floor(#k)\nOutput only the plan.")


def parse(text):
    """-> (ops [(k, op, args)], answer ref). Raises PlanError."""
    ops, ans = [], None
    for line in (text or "").replace("`", "").splitlines():
        if not line.strip(): continue
        m = ANSL.match(line)
        if m: ans = int(m.group(1)); continue
        m = LINE.match(line)
        if m: ops.append((int(m.group(1)), m.group(2), m.group(3).strip()))
    if not ops: raise PlanError("no numbered operations ('#1 op(args)')")
    if ans is None: raise PlanError("no final line 'ANSWER #k'")
    return ops, ans


def render(ops, ans):
    return "\n".join(f"#{k} {op}({a})" for k, op, a in ops) + f"\nANSWER #{ans}"


def literals(ops):
    out = []
    for _, op, a in ops:
        for part in [x.strip() for x in a.split(",")]:
            m = WHERE.match(part)
            if m: out.append(m.group(3).strip())
            elif part and not part.startswith("#") and op in ("lookup", "order_details"): out.append(part.strip("'\""))
    return list(dict.fromkeys(x for x in out if x))


class Runtime:
    """Executes a parsed plan on one task with the task's real tools. 0 model calls."""
    def __init__(s, task):
        s.task, s.rec_tool = task, ("lookup" if "lookup" in task["tools"] else "order_details")

    def _keys(s, v):
        if isinstance(v, dict) and not v: return []
        if isinstance(v, dict) and v and all(isinstance(x, dict) for x in v.values()): return sorted(v)
        if isinstance(v, list): return v
        if isinstance(v, str): return [v]
        raise PlanError("expected keys or records")

    def _fetch(s, keys):
        out = {}
        for i in range(0, len(keys), 10):
            obs = run_tool(s.task, s.rec_tool, ", ".join(keys[i:i + 10]))
            if str(obs).startswith("error"): raise PlanError(f"{s.rec_tool}: {obs}")
            for line in str(obs).splitlines():
                k, _, js = line.partition(": ")
                if js.startswith("{"): out[k.strip()] = json.loads(js)
        return out

    def _recs(s, v):
        if isinstance(v, dict) and v and all(isinstance(x, dict) for x in v.values()): return v
        if isinstance(v, dict) and not v: return {}
        return s._fetch(s._keys(v))

    def _expr(s, rec, expr):
        x = 1.0
        for f in expr.split("*"):
            f = f.strip()
            if f not in rec: raise PlanError(f"no field '{f}' (fields: {', '.join(rec)})")
            x *= float(rec[f])
        return x

    def _ref(s, env, a):
        m = re.match(r"^\s*#\s*(\d+)\s*$", a)
        if not m or int(m.group(1)) not in env: raise PlanError(f"bad reference '{a.strip()}'")
        return env[int(m.group(1))]

    def run(s, ops, ans):
        """-> (answer, notes [soft], digest lines). Raises PlanError (hard failure) with the digest so far in .digest."""
        env, digest, notes, cur = {}, [], [], 0
        try:
            for k, op, a in ops:
                cur = k
                args = [x.strip() for x in a.split(",")] if a else []
                if op in s.task["tools"] and op != "calc":
                    if any(x.startswith("#") for x in args):
                        keys = [kk for x in args for kk in (s._keys(s._ref(env, x)) if x.startswith("#") else [x])]
                        v = s._fetch(keys) if op == s.rec_tool else None
                        if v is None: raise PlanError(f"{op} takes a field=value condition, not a reference")
                    else:
                        obs = str(run_tool(s.task, op, a))
                        if obs.startswith("error"): raise PlanError(f"#{k} {op}: {obs}")
                        if op in ("lookup", "order_details"):
                            v = {ln.partition(": ")[0]: json.loads(ln.partition(": ")[2]) for ln in obs.splitlines()
                                 if ln.partition(": ")[2].startswith("{")}
                        else:
                            v = [] if obs == "(none)" else [x.strip() for x in obs.split(",")]
                elif op in ("and", "or"):
                    A, B = s._keys(s._ref(env, args[0])), s._keys(s._ref(env, args[1]))
                    v = [x for x in A if x in B] if op == "and" else list(dict.fromkeys(A + B))
                elif op == "where":
                    R = s._recs(s._ref(env, args[0])); m = WHERE.match(",".join(args[1:]))
                    if not m: raise PlanError(f"#{k} where: use where(#k, field OP value)")
                    f, c, val = m.groups(); v = {}
                    for key, r in R.items():
                        if f not in r: raise PlanError(f"#{k} where: no field '{f}' (fields: {', '.join(r)})")
                        x = r[f]
                        try: ok = CMP[c](float(x), float(val))
                        except (TypeError, ValueError): ok = CMP[c](str(x).lower(), str(val).lower())
                        if ok: v[key] = r
                elif op in ("sum", "avg", "min", "max"):
                    R = s._recs(s._ref(env, args[0])); xs = [s._expr(r, args[1]) for r in R.values()]
                    if not xs: notes.append(f"#{k} {op} of an empty selection")
                    v = {"sum": sum, "avg": lambda z: sum(z) / len(z) if z else 0, "min": lambda z: min(z) if z else 0,
                         "max": lambda z: max(z) if z else 0}[op](xs)
                elif op == "count":
                    v = len(s._keys(s._ref(env, args[0])))
                elif op in ("argmax", "argmin"):
                    src = s._ref(env, args[0])
                    if isinstance(src, dict) and src and not any(isinstance(x, dict) for x in src.values()): sc = src
                    else: sc = {kk: s._expr(r, args[1]) for kk, r in s._recs(src).items()} if len(args) > 1 else None
                    if sc is None: raise PlanError(f"#{k} {op}: give the expression to compare")
                    if not sc: raise PlanError(f"#{k} {op} of an empty selection")
                    best = (max if op == "argmax" else min)(sc.values()); v = sorted(kk for kk, x in sc.items() if x == best)[0]
                elif op == "group":
                    R = s._recs(s._ref(env, args[0])); v = collections.defaultdict(float)
                    for r in R.values():
                        if args[1] not in r: raise PlanError(f"#{k} group: no field '{args[1]}'")
                        v[str(r[args[1]])] += s._expr(r, args[2])
                    v = dict(v)
                elif op == "calc":
                    e = re.sub(r"#\s*(\d+)", lambda m: repr(float(s._ref(env, "#" + m.group(1)))), a); v = calc(e)
                elif op == "floor":
                    v = math.floor(float(s._ref(env, args[0])))
                else:
                    raise PlanError(f"#{k} unknown operation '{op}'")
                env[k] = v; digest.append(f"#{k} {op}: " + s._size(v))
                if isinstance(v, (list, dict)) and not v: notes.append(f"#{k} {op} selected nothing")
            if ans not in env: raise PlanError(f"ANSWER #{ans} refers to no line")
            v = env[ans]
            if isinstance(v, list) and len(v) == 1: v = v[0]
            if isinstance(v, (list, dict)): raise PlanError(f"ANSWER #{ans} is not one value ({s._size(v)})")
            if isinstance(v, float) and v.is_integer(): v = int(v)
            return str(v if not isinstance(v, float) else round(v, 6)), notes, digest
        except PlanError as e:
            e.digest = digest; raise
        except (IndexError, KeyError, ValueError, TypeError, ZeroDivisionError) as e:
            # never the exception text: it can carry a data value (blindness of the planner)
            pe = PlanError(f"#{cur} cannot be computed ({type(e).__name__}: a field is not numeric, a reference is missing "
                           "or an argument is malformed)"); pe.digest = digest; raise pe

    @staticmethod
    def _size(v):
        if isinstance(v, dict) and v and all(isinstance(x, dict) for x in v.values()):
            return f"{len(v)} records (fields {', '.join(next(iter(v.values())))})"
        if isinstance(v, dict): return f"{len(v)} groups" if v else "0 records"
        if isinstance(v, list): return f"{len(v)} keys"
        return "number" if isinstance(v, (int, float)) else "one key"


def replan_message(task, plan_text, reason, digest):
    """HOLOGRAM CONTEXT: keys + digest, never the transcript, never a value."""
    return ("Task: " + task["question"] + "\nYour plan:\n" + (plan_text or "(none)") + "\nRuntime report (kinds and sizes, no "
            "values):\n" + ("\n".join(digest) if digest else "(nothing ran)") + f"\nRejected: {reason}\n"
            "Write the corrected plan (if the plan is right as it stands, repeat it unchanged).")


# ---------------- PLAN POOL: shapes ----------------
def shape(question, ops, ans):
    """-> (shape regex, plan template) or None. Slots = literals that occur as words in the question."""
    lits = [l for l in literals(ops) if re.search(r"(?<![\w])" + re.escape(l) + r"(?![\w])", question)]
    txt = render(ops, ans); q = question; pos = []
    for l in lits:
        m = re.search(r"(?<![\w])" + re.escape(l) + r"(?![\w])", q)
        if m: pos.append((m.start(), m.end(), l))
    pos.sort(); rx, last = "", 0; tpl = txt
    for i, (a, b, l) in enumerate(pos):
        rx += re.escape(q[last:a]) + r"([\w.-]+)"; last = b
        tpl = re.sub(r"(?<![\w#])" + re.escape(l) + r"(?![\w])", "{{%d}}" % i, tpl)
    rx += re.escape(q[last:])
    return rx, tpl


def pool_match(spec, family, question):
    for (sp, fam, rx), e in PLAN_POOL.items():
        if sp != spec or fam != family: continue
        m = re.fullmatch(rx, question)
        if m:
            t = e["plan"]
            for i, g in enumerate(m.groups()): t = t.replace("{{%d}}" % i, g)
            return (sp, fam, rx), t
    return None, None


def pool_record(spec, family, question, plan_text, confirmed):
    try: ops, ans = parse(plan_text)
    except PlanError: return
    rx, tpl = shape(question, ops, ans); key = (spec, family, rx)
    if key not in PLAN_POOL:
        if not confirmed: return
        PLAN_POOL[key] = {"plan": tpl, "uses": 0, "exec_ok": 0, "agree": 0, "disagree": 0}
    e = PLAN_POOL[key]; e["agree" if confirmed else "disagree"] += 1
    if e["disagree"] > e["agree"]: del PLAN_POOL[key]


# ---------------- MOCK planner (STAND-IN for the interface check only, never for results) ----------------
def mock_plan(task, rng, p_right):
    """A scripted planner: the right plan for the question with p_right, else an executable near-miss; 15% a format error."""
    q = task["question"]; w = lambda rx: re.search(rx, q).group(1)
    if task["family"] == "staff":
        if q.startswith("What is the total salary"):
            P = ("#1 filter(dept={})\n#2 lookup(#1)\n#3 where(#2, years > {})\n#4 sum(#3, salary)\nANSWER #4"
                 .format(w(r"of all (\w+) employees"), w(r"more than (\d+) years")))
        elif q.startswith("Who is the highest"):
            P = "#1 filter(city={})\n#2 lookup(#1)\n#3 argmax(#2, salary)\nANSWER #3".format(w(r"employee in (\w+)\?"))
        elif q.startswith("How many"):
            P = ("#1 filter(dept={})\n#2 filter(city={})\n#3 and(#1, #2)\n#4 lookup(#3)\n#5 where(#4, salary > {})\n"
                 "#6 count(#5)\nANSWER #6").format(w(r"How many (\w+) "), w(r"employees in (\w+) "), w(r"more than (\d+)"))
        else:
            P = "#1 filter(dept={})\n#2 lookup(#1)\n#3 avg(#2, years)\n#4 floor(#3)\nANSWER #4".format(w(r"of (\w+) employees"))
    else:
        if q.startswith("What is the total value"):
            P = ("#1 orders_where(product={})\n#2 order_details(#1)\n#3 where(#2, status=shipped)\n#4 where(#3, city={})\n"
                 "#5 sum(#4, qty*price)\nANSWER #5").format(w(r"shipped (\w+) orders"), w(r"customers in (\w+)\?"))
        elif q.startswith("Which customer"):
            P = "#1 orders_where(status=shipped)\n#2 order_details(#1)\n#3 group(#2, customer, qty*price)\n#4 argmax(#3)\nANSWER #4"
        elif q.startswith("For product"):
            P = ("#1 orders_where(product={})\n#2 order_details(#1)\n#3 where(#2, status=shipped)\n#4 sum(#3, qty*price)\n"
                 "#5 where(#2, status=refunded)\n#6 sum(#5, qty*price)\n#7 calc(#4 - #6)\nANSWER #7").format(w(r"For product (\w+):"))
        else:
            P = ("#1 orders_where(product={})\n#2 order_details(#1)\n#3 where(#2, status=refunded)\n#4 where(#3, city={})\n"
                 "#5 sum(#4, qty)\nANSWER #5").format(w(r"units of (\w+) were"), w(r"customers in (\w+)\?"))
    u = rng.random()
    if u < 0.15: return P.replace("\nANSWER", "\nRESULT")                      # format error (detected by the runtime)
    if u < 0.15 + 0.85 * (1 - p_right):                                       # executable near-miss (not detectable)
        for a, b in ((" > ", " >= "), ("argmax", "argmin"), ("floor(#3)", "calc(#3 + 1)"), ("qty*price", "price")):
            if a in P: return P.replace(a, b, 1)
    return P
