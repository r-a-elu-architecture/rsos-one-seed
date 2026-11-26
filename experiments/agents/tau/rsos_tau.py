"""RSOS structure as a tau-bench (tau2/tau3, sierra-research/tau2-bench) agent. PREPARED 22 Nov 2026, NOT YET SEALED:
the structure code (which roles are on) is fixed by phase 1d and sealed in a separate pre-registration before any run.

The agent is the official LLMAgent (tau-bench's standard tool-calling agent, the leaderboard baseline) plus the roles,
mapped to a customer-service conversation:
  barrier  a tool call identical (name + arguments) to one that already returned an error is not sent; the agent is
           asked once for a different action
  detect   before a WRITE tool call (one that changes the database: book, cancel, refund, modify ...) one verification
           call checks it against the policy and the conversation: VERDICT: OK / WRONG because ...
  adapt    a WRONG verdict makes the agent re-plan and choose again (without adapt it is only told, then chooses again)
  memory   after a WRONG verdict a one-line general lesson is stored; the last 5 lessons of the same domain are added to
           the system prompt of later conversations in this process
  reg      after 30 agent actions in one conversation the agent is told to finish (resolve, or transfer per policy)
Every extra call is an ordinary LLM call through tau2's own generate(); nothing reads the task, the user's
instructions or the expected actions. Registered names: rsos_<code> for the codes below, plus tau2's built-in llm_agent.

Usage (inside a tau2-bench checkout, after `uv sync`):
  uv run python /path/to/rsos_tau.py run --domain retail --agent rsos_11011 --agent-llm openrouter/openai/gpt-oss-20b \
      --user-llm openrouter/openai/gpt-oss-120b --num-trials 1 --task-split-name test --max-concurrency 4
(every argument after the script name is passed to tau2's own CLI, which then sees the extra agents)."""
import sys, threading, json
from typing import Optional
from tau2.agent.llm_agent import LLMAgent
from tau2.data_model.message import AssistantMessage, MultiToolMessage, SystemMessage, ToolMessage, UserMessage
from tau2.utils.llm_utils import generate

CODES = ["11011", "11111", "01100", "11110", "10000", "01000"]
ROLES = ["barrier", "detect", "adapt", "memory", "reg"]
REG_AFTER = 30
_LESSONS, _LOCK = {}, threading.Lock()


def _is_write(tool) -> bool:
    f = getattr(tool, "_func", None)
    return bool(getattr(f, "__mutates_state__", False)) if f is not None else False


def _key(tc) -> str:
    return tc.name + json.dumps(tc.arguments, sort_keys=True, default=str)


class RSOSAgent(LLMAgent):
    def __init__(self, tools, domain_policy, llm, llm_args=None, code="11011", domain="?", **kw):
        super().__init__(tools=tools, domain_policy=domain_policy, llm=llm, llm_args=llm_args, **kw)
        self.roles = dict(zip(ROLES, map(int, code))); self.domain = domain
        self.writes = {t.name for t in tools if _is_write(t)}
        self.failed = {}; self.actions = 0; self.log = []

    def get_init_state(self, message_history=None):
        st = super().get_init_state(message_history)
        if self.roles["memory"]:
            with _LOCK: lessons = list(_LESSONS.get(self.domain, []))[-5:]
            if lessons:
                st.system_messages = st.system_messages + [SystemMessage(role="system", content=
                    "Lessons from earlier conversations (general, apply only if relevant):\n" + "\n".join("- " + l for l in lessons))]
        return st

    def _gen(self, state, extra=None, tools=True, name="agent_response"):
        msgs = state.system_messages + state.messages + ([UserMessage(role="user", content=extra)] if extra else [])
        return generate(model=self.llm, tools=self.tools if tools else [], messages=msgs, call_name=name, **self.llm_args)

    def _generate_next_message(self, message, state) -> AssistantMessage:
        if isinstance(message, MultiToolMessage): new = list(message.tool_messages); state.messages.extend(new)
        else: new = [message]; state.messages.append(message)
        for m in new:  # remember failed calls (barrier)
            if isinstance(m, ToolMessage) and m.error:
                for prev in reversed(state.messages):
                    if isinstance(prev, AssistantMessage) and prev.tool_calls:
                        for tc in prev.tool_calls:
                            if tc.id == m.id: self.failed[_key(tc)] = str(m.content)[:200]
                        break
        note = None
        if self.roles["reg"] and self.actions >= REG_AFTER:
            note = "You have taken many actions in this conversation. Finish now: resolve the request or, if the policy says so, transfer to a human agent."
        out = self._gen(state, note)
        for _ in range(2):  # at most two corrections per turn
            tcs = out.tool_calls or []
            if self.roles["barrier"] and any(_key(tc) in self.failed for tc in tcs):
                tc = next(tc for tc in tcs if _key(tc) in self.failed)
                self.log.append("barrier"); out = self._gen(state, f"Your intended call {tc.name}({tc.arguments}) already failed with: "
                                                             f"{self.failed[_key(tc)]}. Do not repeat it; choose a different action."); continue
            if self.roles["detect"] and any(tc.name in self.writes for tc in tcs):
                tc = next(tc for tc in tcs if tc.name in self.writes)
                v = self._gen(state, f"Before executing it, check this action against the policy and everything the user has said and "
                                     f"confirmed: {tc.name}({json.dumps(tc.arguments, default=str)}). Check the policy's conditions, the "
                                     "exact ids and values, and whether the user explicitly confirmed. Reply with one final line: "
                                     "VERDICT: OK  or  VERDICT: WRONG because <reason>", tools=False, name="rsos_verify")
                vt = str(v.content or "")
                if "VERDICT: WRONG" in vt.upper():
                    reason = vt.upper().split("VERDICT: WRONG", 1)[-1][:300]; self.log.append("detect_wrong")
                    if self.roles["memory"]:
                        les = self._gen(state, f"A check found a problem with an intended action ({reason}). In one line starting "
                                        "with LESSON:, state a general lesson for future conversations (no ids, names or amounts).",
                                        tools=False, name="rsos_lesson")
                        t = str(les.content or "")
                        if "LESSON:" in t:
                            with _LOCK: _LESSONS.setdefault(self.domain, []).append(t.split("LESSON:", 1)[1].strip()[:200])
                    out = self._gen(state, ("The check found a problem:" + reason + (" Re-plan: decide what the policy requires "
                                    "now (ask, confirm, look up, or a different action), then act." if self.roles["adapt"] else " Continue.")))
                    continue
            break
        self.actions += len(out.tool_calls or [])
        return out


def _factory(code):
    def create(tools, domain_policy, **kw):
        task = kw.get("task"); dom = getattr(task, "domain", None) or kw.get("domain") or "?"
        return RSOSAgent(tools=tools, domain_policy=domain_policy, llm=kw.get("llm"), llm_args=kw.get("llm_args"), code=code, domain=str(dom))
    return create


def register():
    from tau2.registry import registry
    for c in sorted(set(CODES)):
        registry.register_agent_factory(_factory(c), f"rsos_{c}")
    try:  # second baseline: tau2's own ReAct example agent (examples/agents/react_agent.py in the checkout)
        import importlib.util, os
        p = os.path.join(os.getcwd(), "examples", "agents", "react_agent.py")
        spec = importlib.util.spec_from_file_location("tau2_react_example", p); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        registry.register_agent_factory(m.create_react_agent, "react_example")
    except Exception as e:
        print("react_example not registered:", e, file=sys.stderr)


if __name__ == "__main__":
    register()
    from tau2.cli import main
    main()
