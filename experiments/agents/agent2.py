"""rsos v2 agent (23 Nov 2026), built from the phase 3 diagnosis (diag/DIAG_PHASE3_OUT.txt).
agent.py, llm.py, run.py and tasks.py are sealed (SEAL_AGENTS_PHASE3) and are NOT edited: this module reuses them unchanged.

Phase 3: rsos_01100 (detect + adapt only; barrier, memory and regulation off) lost 75 tasks to react. Its own actions
helped in 6 and hurt in about 37: 19 losses gave no answer (call or token budget used up by verification and re-plans),
8 drifted through repeated actions, 3 had a right answer thrown away by an unsupported WRONG verdict, and 17 runs ended with
nothing although an answer had been given earlier. rsos2 adds exactly the missing parts:

  barrier   an action identical to one already run is not executed again (the earlier result is returned)       [phase 3: off]
  reg2      budget-aware regulation: verification runs only if, after it, at least 2 calls and 3,000 tokens remain;
            when 2 calls or fewer (or under 3,000 tokens) remain, the agent is told once to answer now              [new]
  detect2   verification must name the observation it contradicts: a WRONG verdict counts only if its reason
            contains a number or name that appears in the tool results; otherwise the answer stands             [new]
  adapt     a counted WRONG verdict makes the agent re-plan; at most one re-plan per task                       [as phase 3]
  fallback  if the run ends without a final answer, the last answer given earlier is returned                    [new]
  memory    off (tasks stay independent)

Arms provided here: rsos2 (the structure above), react_b (react exactly as agent.py, a second label for the noise floor).
Every other arm is passed to agent.run_arm unchanged."""
import re
import agent
from agent import Budget, system_prompt, last_line, ACT, ANS, MAX_CALLS
from tasks import run_tool
import llm

TOK_RESERVE = 3000
WORD = re.compile(r"[A-Za-z][a-z]{2,}|\d[\d.,]*")

class Budget2(Budget):
    """Same accounting as agent.Budget; the trace also records which OpenRouter provider served each call."""
    def call(s, *a, **k):
        llm.LAST.pop("provider", None); txt = super().call(*a, **k)
        if llm.LAST.get("provider"): s.log[-1]["provider"] = llm.LAST["provider"]
        return txt
    def left(s): return MAX_CALLS - s.calls, agent.MAX_TOK - s.tok

def supported(reason, observations):
    """detect2: the WRONG reason must cite something that is in the tool results (a number or a name)."""
    obs = " ".join(observations); toks = {t.rstrip(".,") for t in WORD.findall(reason)}
    nums = {t for t in toks if t[0].isdigit()}; names = {t for t in toks if t[0].isupper()}
    return any(n in obs for n in nums) or any(n in obs for n in names)

def rsos2(task, spec, B):
    system = system_prompt(task); msgs = [{"role": "user", "content": "Task: " + task["question"]}]
    seen = {}; observations = []; best = None; replanned = False; warned = False
    while B.ok():
        calls_left, tok_left = B.left()
        if not warned and (calls_left <= 2 or tok_left < TOK_RESERVE):
            msgs.append({"role": "user", "content": "Budget nearly used: give your best ANSWER now."}); warned = True
        txt = B.call(spec, system, msgs); msgs.append({"role": "assistant", "content": txt})
        a = last_line(txt, ANS)
        if a and not last_line(txt, ACT):
            ans = a.group(1); best = ans
            calls_left, tok_left = B.left()
            if not replanned and calls_left - 1 >= 2 and tok_left > TOK_RESERVE * 2:
                v = B.call(spec, system, msgs + [{"role": "user", "content": "Verify your answer step by step against the tool "
                           "results above. Reply with one final line: VERDICT: OK  or  VERDICT: WRONG because <the tool result it "
                           "contradicts, quoted>"}])
                if "VERDICT: WRONG" in v.upper():
                    reason = v[v.upper().index("VERDICT: WRONG") + 14:][:300]
                    if supported(reason, observations):
                        replanned = True
                        msgs.append({"role": "user", "content": "Verification failed:" + reason +
                                     "\nRe-plan: state a new plan in one line, then continue with ACTION or ANSWER."})
                        continue
            return ans
        m = last_line(txt, ACT)
        if not m:
            msgs.append({"role": "user", "content": "Reply must end with one line: ACTION: tool(arguments) or ANSWER: value"}); continue
        key = (m.group(1), m.group(2).strip())
        if key in seen:
            obs = ("BLOCKED: this exact action already failed (" + seen[key][:120] + "). Change approach." if seen[key].startswith("error")
                   else "BLOCKED: already done, result was: " + seen[key][:300])
        else:
            obs = run_tool(task, key[0], key[1]); seen[key] = obs; observations.append(obs)
        msgs.append({"role": "user", "content": "Observation: " + obs})
    return best  # fallback: the last answer given, if any

def rsos3(task, spec, B):
    """rsos3 (23 Nov 03:35) = rsos2 with two changes from the quick2 diagnosis (diag/DIAG_QUICK2.md):
    counter-shift  (P1 from ORG7, moved to the agent host): the part with the longest failing run gets the help. When 2 or
                   more tool results in a row are errors or blocked repeats, the next observation carries the exact tool
                   usage plus the order filter/lookup -> calc with plain numbers (Llama: runs with such a streak were
                   17/34 correct, without 134/146).
    late regulation: 'answer now' only on the last call (or under 2,000 tokens left), not 2 calls early (quick2: the early
                   prompt cut 3 runs that react finished correctly)."""
    system = system_prompt(task); msgs = [{"role": "user", "content": "Task: " + task["question"]}]
    seen = {}; observations = []; best = None; replanned = False; warned = False; streak = 0
    from tasks import TOOL_HELP
    usage = "\n".join("- " + TOOL_HELP[t] for t in task["tools"])
    while B.ok():
        calls_left, tok_left = B.left()
        if not warned and (calls_left <= 1 or tok_left < 2000):
            msgs.append({"role": "user", "content": "Last call: give your best ANSWER now."}); warned = True
        txt = B.call(spec, system, msgs); msgs.append({"role": "assistant", "content": txt})
        a = last_line(txt, ANS)
        if a and not last_line(txt, ACT):
            ans = a.group(1); best = ans
            calls_left, tok_left = B.left()
            if not replanned and calls_left - 1 >= 2 and tok_left > TOK_RESERVE * 2:
                v = B.call(spec, system, msgs + [{"role": "user", "content": "Verify your answer step by step against the tool "
                           "results above. Reply with one final line: VERDICT: OK  or  VERDICT: WRONG because <the tool result it "
                           "contradicts, quoted>"}])
                if "VERDICT: WRONG" in v.upper():
                    reason = v[v.upper().index("VERDICT: WRONG") + 14:][:300]
                    if supported(reason, observations):
                        replanned = True
                        msgs.append({"role": "user", "content": "Verification failed:" + reason +
                                     "\nRe-plan: state a new plan in one line, then continue with ACTION or ANSWER."})
                        continue
            return ans
        m = last_line(txt, ACT)
        if not m:
            msgs.append({"role": "user", "content": "Reply must end with one line: ACTION: tool(arguments) or ANSWER: value"}); continue
        key = (m.group(1), m.group(2).strip())
        if key in seen:
            obs = ("BLOCKED: this exact action already failed (" + seen[key][:120] + "). Change approach." if seen[key].startswith("error")
                   else "BLOCKED: already done, result was: " + seen[key][:300])
        else:
            obs = run_tool(task, key[0], key[1]); seen[key] = obs; observations.append(obs)
        streak = streak + 1 if (obs.startswith("error") or obs.startswith("BLOCKED: this exact action already failed")) else 0
        if streak >= 2:
            obs += ("\nCounter-shift: the last " + str(streak) + " actions failed. Each tool takes only what its line says:\n" + usage +
                    "\nGet names with the selection tool, then their records, then pass plain numbers to calc. Never nest tools.")
        msgs.append({"role": "user", "content": "Observation: " + obs})
    return best

def run_arm(arm, task, spec, stream):
    if arm == "rsos3":
        B = Budget2(); B.tools = task["tools"]; return rsos3(task, spec, B), B
    if arm == "rsos2":
        B = Budget2(); B.tools = task["tools"]; return rsos2(task, spec, B), B
    if arm == "react_b":
        return agent.run_arm("react", task, spec, stream)
    return agent.run_arm(arm, task, spec, stream)
