"""Agent arms on one harness, one model, one budget per task (max 12 model calls and 12,000 tokens in+out).
Baselines (faithful re-implementations of the patterns the frameworks run by default; the framework packages are not
used in this 12-hour version):
  plain      one call, reasoning, no tools
  react      thought -> ACTION -> observation loop (the LangGraph / AutoGen default agent pattern)
  reflexion  react; then a self-verification; if judged wrong, one retry with the reflection (Reflexion pattern)
  selfcons   3 react attempts at temperature 0.7 within the same budget, majority answer (self-consistency)
  planexec   a plan first, then react with the plan (plan-and-execute pattern)
RSOS structure: react plus the roles of the family structure, code = barrier detect adapt memory reg (as in ORG5 real):
  barrier  an action identical to one that already failed or already ran is blocked (no repeated failure)
  detect   before an answer is accepted, one verification against the trace (VERDICT: OK / WRONG because ...)
  adapt    a failed verification makes the agent re-plan (otherwise it is only told and continues)
  memory   lessons from earlier tasks' failures are carried into later tasks of the same stream (last 5)
  reg      regulation: when 2/3 of the call budget is used, the agent is told to answer now; no verification when the
           budget is nearly spent"""
import re, collections
from llm import chat, LAST
from tasks import run_tool, TOOL_HELP

import os
MAX_CALLS = 12
MAX_TOK = int(os.environ.get("AGENT_MAX_TOK", "12000"))     # phase 1b and later: 16000 (sealed)
REPLY_TOK = int(os.environ.get("AGENT_REPLY_TOK", "700"))   # phase 1b and later: 1500 (sealed); phase 1 used 700
ACT = re.compile(r"ACTION:\s*(\w+)\s*\((.*)\)\s*$", re.S)
ANS = re.compile(r"ANSWER:\s*(.+?)\s*$", re.S)

class Budget:
    def __init__(s): s.calls = 0; s.tok = 0; s.log = []
    def ok(s, need=1): return s.calls + need <= MAX_CALLS and s.tok < MAX_TOK
    tools = None  # tool names declared natively (design v3); None for plain
    def call(s, spec, system, msgs, temperature=0.0, max_tokens=None):
        max_tokens = max_tokens or REPLY_TOK
        LAST.pop("reasoning", None)
        txt, i, o = chat(spec, system, msgs, max_tokens=max_tokens, temperature=temperature, tools=s.tools); s.calls += 1; s.tok += i + o
        s.log.append({"in": msgs[-1]["content"][-400:], "out": txt[-600:], "finish": LAST.get("finish"), **({"reasoning": LAST["reasoning"]} if LAST.get("reasoning") else {})}); return txt

def system_prompt(task, lessons=None):
    tools = "\n".join("- " + TOOL_HELP[t] for t in task["tools"])
    s = ("You solve the task with tools. Each reply: brief reasoning, then exactly one final line, either\n"
         "ACTION: tool(arguments)\nor\nANSWER: value\nTools:\n" + tools + "\nGive only the value after ANSWER (a number or a name).")
    if lessons: s += "\nLessons from earlier tasks:\n" + "\n".join("- " + l for l in lessons[-5:])
    return s

def last_line(txt, rx):
    for line in reversed([l for l in txt.strip().splitlines() if l.strip()]):
        m = rx.search(line.strip())
        if m: return m
    return None

def react(task, spec, B, system, msgs, temperature=0.0, roles=None, stream=None):
    roles = roles or {}; seen = {}; failed = False; verdict_fail = None
    while B.ok():
        if roles.get("reg") and B.calls >= (2 * MAX_CALLS) // 3 and not msgs[-1]["content"].startswith("Budget"):
            msgs.append({"role": "user", "content": "Budget nearly used: give your best ANSWER now."})
        txt = B.call(spec, system, msgs, temperature); msgs.append({"role": "assistant", "content": txt})
        a = last_line(txt, ANS)
        if a and not last_line(txt, ACT):
            ans = a.group(1)
            if roles.get("detect") and B.ok(2 if roles.get("reg") else 1):
                v = B.call(spec, system, msgs + [{"role": "user", "content": "Verify your answer step by step against the tool results above. "
                           "Reply with one final line: VERDICT: OK  or  VERDICT: WRONG because <reason>"}])
                if "VERDICT: WRONG" in v.upper():
                    failed = True; verdict_fail = v.split("WRONG", 1)[-1][:300]
                    msgs.append({"role": "user", "content": ("Verification failed:" + verdict_fail +
                                 ("\nRe-plan: state a new plan in one line, then continue with ACTION or ANSWER." if roles.get("adapt") else "\nContinue."))})
                    continue
            return ans, failed
        m = last_line(txt, ACT)
        if not m:
            msgs.append({"role": "user", "content": "Reply must end with one line: ACTION: tool(arguments) or ANSWER: value"}); continue
        key = (m.group(1), m.group(2).strip())
        if roles.get("barrier") and key in seen:
            obs = ("BLOCKED: this exact action already failed (" + seen[key][:120] + "). Change approach." if seen[key].startswith("error")
                   else "BLOCKED: already done, result was: " + seen[key][:300])
        else:
            obs = run_tool(task, key[0], key[1]); seen[key] = obs
        if obs.startswith("error"): failed = True
        msgs.append({"role": "user", "content": "Observation: " + obs})
    return None, True

def run_arm(arm, task, spec, stream):
    """stream: dict kept across the tasks of one (model, arm) run; holds lessons for the memory role."""
    B = Budget(); q = {"role": "user", "content": "Task: " + task["question"]}
    if arm != "plain": B.tools = task["tools"]
    if arm == "plain":
        txt = B.call(spec, "Solve the problem. Reason briefly, then end with one line: ANSWER: value", [q])
        a = last_line(txt, ANS); return (a.group(1) if a else None), B
    if arm == "react":
        return react(task, spec, B, system_prompt(task), [q])[0], B
    if arm == "planexec":
        p = B.call(spec, system_prompt(task), [q, {"role": "user", "content": "First write a numbered PLAN only (no actions yet)."}])
        return react(task, spec, B, system_prompt(task), [q, {"role": "assistant", "content": p}, {"role": "user", "content": "Now execute the plan."}])[0], B
    if arm == "reflexion":
        msgs = [q]; ans, _ = react(task, spec, B, system_prompt(task), msgs)
        if ans is None or not B.ok(2): return ans, B
        v = B.call(spec, system_prompt(task), msgs + [{"role": "user", "content": "Verify your answer step by step. Final line: VERDICT: OK  or  VERDICT: WRONG because <reason>"}])
        if "VERDICT: WRONG" not in v.upper(): return ans, B
        refl = B.call(spec, system_prompt(task), msgs + [{"role": "assistant", "content": v}, {"role": "user", "content": "Write a short reflection: what went wrong and what to do differently."}])
        a2, _ = react(task, spec, B, system_prompt(task), [q, {"role": "user", "content": "Reflection from a previous attempt: " + refl[:600]}])
        return (a2 if a2 is not None else ans), B
    if arm == "selfcons":
        votes = []
        for _ in range(3):
            if not B.ok(): break
            a, _ = react(task, spec, B, system_prompt(task), [q], temperature=0.7)
            if a is not None: votes.append(a.strip().rstrip("."))
        return (collections.Counter(votes).most_common(1)[0][0] if votes else None), B
    if arm.startswith("rsos_"):
        code = arm[5:]; roles = dict(zip(["barrier", "detect", "adapt", "memory", "reg"], map(int, code)))
        lessons = stream.setdefault("lessons", []) if roles["memory"] else None
        msgs = [q]; ans, failed = react(task, spec, B, system_prompt(task, lessons), msgs, roles=roles)
        if roles["memory"] and failed and B.ok():
            l = B.call(spec, system_prompt(task), msgs + [{"role": "user", "content": "In one line starting with LESSON:, state a general lesson for future tasks (no task-specific numbers)."}], max_tokens=min(400, REPLY_TOK))
            m = re.search(r"LESSON:\s*(.+)", l)
            if m: lessons.append(m.group(1).strip()[:200])
        return ans, B
    raise ValueError(arm)
