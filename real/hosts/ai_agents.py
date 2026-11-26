"""REAL1 row 1 "ai_agents": AI agents on real models (OpenRouter on the laptop; `mock:0` here for the interface check).

HOST
  Episode (one cell) = 4 tool-use tasks of the phase-3 families (experiments/agents/tasks.py, unchanged): staff, orders,
  staff, orders, generated from NEW seeds 7_000_000 + 10*cell + k (never used before: phase 3 used staff 5000-5149, orders
  3000-3149). Development cells 1..4; the confirmatory cells are fixed by the lead in the seal.
  Units = reasoning branches of the current task (independent ReAct attempts, at most 3) and their candidate next steps.
  Budget = the phase-3 harness budget per task (design v3): at most 12 model calls and 16,000 tokens (in+out), replies up to
  1,500 tokens, tools declared natively. valid() enforces it: when the budget is spent the task is committed.
  One step = at most one model call (the same budget as the standard action).
  Actions: ("step", b)        the next ReAct step of branch b (thought -> ACTION -> observation, or ANSWER)
           ("new",)           open a new branch (fresh attempt, temperature 0.7) and take its first step
           ("restart", b)     focused: drop branch b's context and take the first step of a fresh attempt at temperature 0.7
                              in its place (same id; the task's budget keeps counting). Offered only for what the tree
                              records: a temperature-0 ReAct attempt, unanswered after k >= 1 calls, restarted at most once,
                              at a state (k, e) where the paired record favours the restart (sign test p <= ALPHA = 0.10)
           ("cross", b, src)  coupled: branch b's next step, told the answer of branch src (branches driving each other)
           ("commit",)        end the task with the majority answer of the answered branches (no call)
  Result = task accuracy (tasks.correct against the exact answer); resource = kilotokens (in+out, every call). The seed
  makes NO extra calls (24 Nov: the forecast calls are gone; the own future is read from the real tree). R = accuracy per
  kilotoken. Free-resource row: pass per cell = Pareto (result >= standard AND resource <= standard, one strictly).

STANDARD METHOD (default = the baseline and the membrane bound), faithful to experiments/agents/agent.py (phase 3, sealed):
  standard="react"     ReAct (Yao et al. 2022) exactly as agent.react with no roles: branch 0 at temperature 0 steps until
                       it gives ANSWER (an ANSWER line with no ACTION line) or the budget is spent; then commit.
  standard="selfcons"  self-consistency (Wang et al. 2022) exactly as agent.run_arm("selfcons"): up to 3 ReAct attempts at
                       temperature 0.7 inside the same budget, sequentially; majority answer (Counter.most_common).
  Phase-3 reference (sealed, 1,200 units per arm): react 0.871 accuracy, 4,149 tokens per task; selfcons 0.887, 9,316.
  (Unchanged on 24 Nov. After a restart the standard continues "branch 0" / "the latest attempt" as before, which is then
  the fresh attempt: default() itself is not changed.)

THE HOST'S OWN MODEL = THE REAL TREE (fork; layer-1 rule; 24 Nov)
  real/hosts/data/ai_agents_tree.json, built by real/hosts/ai_agents_tree.py from the recorded phase-3 / quick2 / quick3
  runs of real models (2,880 plain-ReAct and self-consistency records; task seeds 3000-6129, never the 7,000,000+ test
  seeds). Every call of every recorded attempt is a node: (model, family, temperature, k = calls made in the attempt,
  e = an error observation or format note so far, prev = outcomes of the earlier attempts on the task). A node holds what
  REALLY followed: further calls until the answer (or none before the budget ran out), whether the answer was right, and
  the expected remaining tokens. Thin nodes (n < 20) back off: drop prev, then pool models, then pool families, then the
  nearest smaller k. The model key is the run's model spec when the tree has it (gpt-oss-20b, gpt-oss-120b, llama-4-scout,
  qwen3.8-27b), otherwise the pooled "*" (also for mock:0).
  fork(state, j): randomness default_rng([cell, t, j, 7331]) (independent of the real step; all branches of one decision
  share it: every uniform is drawn up front, so candidates are compared on common random numbers).
    1. Answered branches: which of their distinct answers is right (or none) is drawn from the posterior of the tree:
       P(right | temperature, call of the answer, e, prev) per answer (tree "ans"), agreement between attempts, and the
       recorded rate at which two wrong answers coincide (tree "collide").
    2. Unanswered branches: (further calls r, right?) drawn from the tree node of their current state (prev = the latent
       outcomes of the lower branches; a temperature-0.7 branch next to one temperature-0 ReAct branch uses the paired
       record: self-consistency attempt 0 on the tasks where ReAct gave that outcome).
    3. Branches that do not exist yet ("new"): the node of a fresh temperature-0.7 attempt given the latent prev.
    4. A restart of branch b at state (k, e): the tree "restart" node = the paired self-consistency attempt 0 on exactly
       the tasks where ReAct was still unanswered after k calls with error state e (the real record of abandoning a stuck
       ReAct context and starting afresh); drawn with the same uniforms as the continuation (coupled comparison). A
       restarted branch keeps reading that node, given that it is still unanswered after its own calls.
    Tokens per simulated call: the branch's last real call + the tree's per-call growth g (a new or restarted attempt:
    the task's observed first call, else the tree's a). Cross steps are valued as plain steps (no record of the hint).
  objective(state) = (estimated accuracy of the episode, -tokens), lexicographic (the row's value rule, unchanged). In a
  fork the current task counts 1 if the majority answer (Counter order, as committed) is the latent right one, else 0;
  the mean over the forks is the tree's probability. Committed tasks count the tree posterior P(majority right) at commit
  (a constant across the candidates of a decision). No ground truth anywhere in the seed's view.
  WHERE THE SEED MAY DEVIATE (owner 24 Nov: only where the real record says the standard's next step tends to fail or
  waste tokens):
    standard react: branches() offers nothing (the seed = ReAct) unless branch 0 is a temperature-0 ReAct attempt at a
      state (k, e) where the paired record says continuing tends to fail: on the same tasks, a fresh attempt was right and
      ReAct wrong significantly more often than the reverse (one-sided exact sign test p <= 0.10 on the node the fork
      reads). For gpt-oss-20b that is staff k = 3, 5, 6, 8+ without errors (and 10+ with), orders k = 8+ with errors.
      Only there are restart / open / focus / cross valued; the fork then picks the best by (accuracy, -tokens).
    standard selfcons: stop (commit, no call) and the other actions are always valued; the typical deviation is to stop
      when further attempts cannot change the majority within the budget (in the tree's read at 64 forks).
  64 forks resolve differences of about 1/64 per task, the order of the tree's own uncertainty (nodes of 100-300
  records); gains smaller than that are not acted on (with 256 forks the seed stops less often under selfcons).

MOCK (`mock:0`, the interface check here; STAND-IN, never for results)
  llm.mock is not deterministic across processes (Python hash randomisation), so the real step's model is replaced by a
  deterministic stand-in: branch b of task i needs 2-5 calls (rng [cell, i, b, 5502], plus the restart count after a
  restart); its answer is right with p 0.82 at T=0 (0.75 at T=0.7), else a near miss; tokens 380 + 160*calls in, 110 out.
  The stand-in world uses the task's answer to produce answers; the seed's model never does. Mock runs read the pooled
  ("*") tree; they check the interface only.

SIZE (rule 5): 4 tasks per cell; horizon 14 simulated steps (covers a whole task: 12 calls + commit); 64 samples per
  decision (tree forks cost microseconds and no tokens). Quick test here (mock, 8 cells x 2 standards x 2 modes): about
  12 s. On the laptop the cost is only the real calls (about 20-40 per cell and mode; the seed adds none).

REAL2 ADDITIONS (24 Nov, brief A-C)
A. LAW 4 LANDINGS. The budget unit of an action = ONE MODEL CALL ON ONE REASONING BRANCH (an action makes at most one
   call, so it has at most one landing; commit / withhold make no call and have none).
     landings(st, a)        [("call", b)] for step / cross / restart of branch b, [("call", n)] for "new" (n = the new id)
     without(st, a, L)      the call withheld: ("commit",) when an answer exists (stop now with the answers in hand),
                            else ("withhold",) = end the task with no answer (no call; scored wrong). Kept only if the own
                            futures say the call is not needed (seed.land: value without >= value with).
     targets(st, a, L)      up to 3 other placements of that call, highest need first: step of another unanswered branch,
                            "new" (a fresh T=0.7 attempt), restart of a branch where _can_restart holds. Need = the tree's
                            P(this attempt ends with a right answer | its state). Under standard react the same gate as
                            branches(): no other placement unless the paired record favours a restart there.
     retarget(st, a, L, T)  the call placed at T instead (same resource: one call).
   The landing test runs in the same own futures as the choice (the real tree, 64 forks): no extra paid call.
C. STRONGEST METHOD standard="strongest": confidence-guided early stopping of self-consistency (CGES, NeurIPS 2025,
   arXiv 2511.02603; with the stage-1 single-sample gate of ReASC, arXiv 2601.02970). Sequential attempts at
   temperature 0.7 inside the same budget as selfcons (at most 3 attempts, 12 calls, 16k tokens). After every answered
   attempt the CGES posterior over the candidate answers is computed (uniform prior; candidates = the distinct answers
   given + one "answer not yet seen", K = their number):
       P(I = i | obs) ∝ prod_t [ C_t if R_t = a_i else (1 - C_t) / (K - 1) ]
   and the task commits as soon as max_i P(I = i | obs) >= GAMMA = 0.95 (ReASC's C_threshold; within CGES's sweep), so
   with one attempt the rule is ReASC's stage-1 gate (accept if C_1 >= 0.95). Final answer = the posterior argmax over the
   given answers (majority order on ties). No token log-probs: the harness does not request them and the OpenRouter
   providers of these models do not return them reliably. C_t is therefore the CALIBRATED RELIABILITY of the attempt's
   answer state from the real records (labelled offline calibration as in ReASC): the tree's "ans" rate
   P(right | model, family, temperature 0.7, call of the answer, error state) (back-off as in Tree.q_ans; prev pooled "-",
   so agreement enters only through the posterior). With constant C_t this is the pure answer-agreement posterior. Same
   data the seed reads; nothing from the test cells; fixed before any comparison was run.
ROBUSTNESS (24 Nov; the Llama 3.1 8B row failed twice in the cloud after ~5 min, error not kept). What can break on that
   model in llm.chat / this host, and what the host now does (llm.py itself is sealed in phase 3 and is not changed):
   - persistent 429 / 5xx from the routed provider: llm._post retries 10 times with back-off 1+2+4+...+60 s = ~5 min, then
     raises LLMError("retries exhausted")  (matches the ~5 min failure);
   - 404 / 400 from a provider that routes without tool support, or that rejects an EMPTY assistant message (an empty
     reply is stored as "" and sent back on the next call);
   - HTTP 200 with an error body and no "choices", or "usage": null (KeyError / TypeError / AttributeError in llm.chat);
   - a tool call with "name": null; tool-call JSON written as TEXT ("<|python_tag|>{"name": ..., "parameters": ...}")
     instead of a native call (no crash, but every such reply cost a call as a format error).
   The host now calls the model through _chat: any exception is logged with its text (per cell, task, branch, call; to
   stderr and report()["errors"]), the call is retried ONCE with empty assistant turns replaced by "(no reply)"; if it
   fails again the task's budget is closed (the task commits with the answers in hand, wrong if none) and the episode goes
   on. A reply with no usage gets a chars/4 estimate (counted in report()["usage_estimated"]). A text tool call in Llama's
   JSON form, or an ACTION whose argument is the JSON {"args": ...}, is rewritten to the text action the harness parses,
   exactly as llm.chat rewrites native tool calls (design v3; counted in report()["text_toolcalls"]). All of this applies
   identically to every mode and standard.
REAL3 (24 Nov; bound to real/seed3.py; REAL1/REAL2 modes give identical numbers, checked on cells 1-8, every mode)
   primitives(st): P4P5 = the strongest method's action here (CGES posterior stop, else the next attempt); P8 = one more
     attempt (a vote of futures) when an answer is in hand.
   frame(st) (runtime + pool in real/hosts/ai_agents_blind.py):
     F:blind  ("blind", b): BLIND PLANNING, the loop of the sealed A7/A8 X5b arm (experiments/a7_arms.py run_plan): ONE
              planner call writes the plan of operations over keys and #references, seeing no data value; the runtime
              calls the task's real tools, computes every value and answers (0 calls); the model is called again only on a
              detected failure (parse, reference, tool error, empty selection, non-scalar answer), at most MAX_RETRY = 2
              re-plans; after that the slot falls back to a fresh ReAct attempt. Offered on a branch before its first
              call, on a ReAct branch where the paired record favours a restart (_can_restart), or as a new slot.
     HOLOGRAM CONTEXT: every re-plan call carries the question, the previous plan, the runtime's reason and a digest of
              kinds and sizes per line, never the transcript and never a value (runtime error texts are not forwarded).
     F:reuse  ("reuse", b): O-trace PLAN REUSE: a plan confirmed at commit (its answer = the committed answer) is pooled
              under the question's shape (process-wide, per model spec and family); a later question of that shape runs
              it with zero calls; contradicted entries are removed. No ground truth anywhere.
     F:vote   when every branch has answered: stop where the tree posterior's top >= GAMMA, one more attempt only where it
              is uncertain.
   coupled(st): True once an answer is in hand and >= 2 branches exist (the committed answer is their joint vote).
   THE OWN MODEL OF A BLIND BRANCH (forks): no recorded blind run exists on these tasks, so a blind plan is valued as
     EXACTLY AS ACCURATE as a fresh attempt of the same model (its rightness is the same tree draw, on the same uniforms,
     as a fresh attempt in that slot; a converted stuck branch reads the restart record); P(answer right) in the
     posterior = the fresh node's P(right | answered). Plan execution succeeds per call with pe = this host's O-trace,
     prior Beta(3, 1); plan / re-plan tokens = the O-trace mean (>= 3 calls), prior tree first-call size + 250 / + 400.
     So the seed prefers blind plans only through tokens unless the trace says they fail to execute; any accuracy effect
     is measured only by the real run. A tree node from recorded blind runs replaces this assumption once they exist.
REAL3 v2 (25 Nov; seed operators, real/HOST_INTERFACE_REAL3v2.md; REAL1/REAL2 modes and seed3v1 byte-identical, checked
   on mock cells 1-4, every mode, full report incl. choices)
   parts      the attempt slots of the current task, id (task index, slot): existing branches + the next empty slot (< 3).
              One step = one call = one slot (the REAL2 landing unit). Tasks are NOT parts: a step acts only on the current
              task. No sub-parts (ENTER depth 1).
   merge      one call per step: the first named slot whose action calls on that slot; else the standard.
   part_objective  P(the slot contributes a right answer) from the real tree (answered: posterior of its answer;
              unanswered: P(attempt ends right | state); empty slot / blind / restarted: the fresh node).
   focus      the one call on slot p (its next step, or a new attempt in the empty slot).
   joint      CROSS (a branch's next call told another branch's answer).
   map_part   the same operation on another slot (step / restart / blind / reuse / cross).
   shape      (standard, family, question type, per-slot kind/answered/calls/error, pooled plan exists).
   op_of      F:reuse -> inherit (O-trace plan reuse), F:blind -> compress (keys only, the runtime computes), F:vote -> vote,
              restart -> heal, open -> explore, cross -> fuse; focus -> beam, P4P5 -> fuse, P8 -> vote by the seed's table.
   carry      NOT bound: the budget is per task (sealed harness: 12 calls / 16k tokens); an unused call is simply not
              spent (fewer tokens) and carrying it to the next task would change the harness budget.
ROBUSTNESS v2 (25 Nov; the Llama 3.1 8B cloud job died after 1h49m with no log): every model call goes through
   llm_bounded.chat (llm.py stays sealed; its _post is swapped for one call only): per request 45 s timeout, <= 4 requests,
   back-off <= 8 s (+ jitter; retry-after capped at 15 s), wall deadline 100 s per call; after 3 consecutive failed calls
   each call gets one 30 s request until one succeeds (circuit breaker). The host's second try is made only for a 400 /
   422 or an unreadable reply, never after a rate-limit / timeout exhaustion. A failed call is logged (cell, task,
   branch, call, reason) and counted (report()["failed_calls"]; 0 tokens: no usage is returned), the task commits with
   the answers in hand, the episode and the job go on.
   Tokens: every plan and re-plan call is counted in resource (report: plan_calls, plan_failures, plans_reused,
     blind_answers, blind_fallbacks). Mock: ai_agents_blind.mock_plan, a scripted STAND-IN (right plan with p 0.82 / 0.75,
     else an executable near-miss; 15% a format error), never for results."""
import os, sys, re, json, math, collections
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
AG = os.path.abspath(os.path.join(HERE, "..", "..", "experiments", "agents"))
if AG not in sys.path: sys.path.insert(0, AG)
import llm                                                    # noqa: E402  (keys from environment only)
from tasks import make, run_tool, correct, NAMES              # noqa: E402
from agent import system_prompt, last_line, ACT, ANS          # noqa: E402
import ai_agents_blind as BL                                  # noqa: E402  (REAL3 frame: blind runtime, plan pool)
import llm_bounded as LB                                      # noqa: E402  (REAL3 v2: bounded calls)

MAX_CALLS, MAX_TOK, REPLY_TOK = 12, 16000, 1500               # design v3 (phase 3, sealed)
TREE_PATH = os.path.join(HERE, "data", "ai_agents_tree.json")
N_MIN = 20                                                    # a tree node is read only with at least 20 recorded states
ALPHA = 0.10                                                  # restart only where the paired record favours it at p <= 0.10
GAMMA = 0.95                                                  # strongest (CGES / ReASC): stop when the top posterior >= 0.95

def norm(a): return str(a).strip().rstrip(".")

_JSON_CALL = re.compile(r"\{[^{}]*\"name\"\s*:\s*\"([\w.]+)\"[^{}]*?\"(?:parameters|arguments)\"\s*:\s*(\{[^{}]*\}|\"[^\"]*\")", re.S)

def _tool_args(nm, d):
    """The argument text of a tool call (the same mapping as llm.chat for native calls)."""
    if isinstance(d, dict) and "args" in d: return str(d["args"])
    if isinstance(d, dict) and {"field", "value"} <= set(d): return f"{d['field']}={d['value']}"
    if isinstance(d, dict) and len(d) == 1 and nm in ("filter", "orders_where"): return f"{list(d)[0]}={list(d.values())[0]}"
    if isinstance(d, dict): return ", ".join(", ".join(map(str, v)) if isinstance(v, list) else str(v) for v in d.values())
    return str(d)

def normalise_reply(txt, tools):
    """Llama-style tool calls written as text -> the text action the harness parses. Returns (text, rewritten?)."""
    if last_line(txt, ANS) or (last_line(txt, ACT) and not last_line(txt, ACT).group(2).strip().startswith("{")):
        return txt, False
    m = last_line(txt, ACT)
    if m:                                                      # ACTION: lookup({"args": "Lior"})
        try: return txt.rstrip() + f"\nACTION: {m.group(1)}({_tool_args(m.group(1), json.loads(m.group(2).strip()))})", True
        except Exception: return txt, False
    for g in reversed(list(_JSON_CALL.finditer(txt))):        # {"name": "lookup", "parameters": {"args": "Lior"}}
        nm = g.group(1).split(".")[-1]
        if nm not in tools: continue
        try: d = json.loads(g.group(2)); d = json.loads(d) if isinstance(d, str) and d.strip().startswith("{") else d
        except Exception: continue
        return txt.rstrip() + f"\nACTION: {nm}({_tool_args(nm, d)})", True
    return txt, False

def majority(votes):
    return collections.Counter(votes).most_common(1)[0][0] if votes else None


class Tree:
    """Read-only view of the real tree with back-off (see ai_agents_tree.py for how it is built)."""
    def __init__(s, path=TREE_PATH):
        if not os.path.exists(path):
            import ai_agents_tree; ai_agents_tree.build()
        t = json.load(open(path)); s.cont, s.ansd, s.rst, s.coll, s.tok = t["cont"], t["ans"], t["restart"], t["collide"], t["tok"]
        s.cache = {}

    def model_key(s, spec):
        return spec if f"{spec}|staff" in s.tok else "*"

    def _cdf(s, key, node):
        if key not in s.cache:
            rs = sorted(node["r"], key=lambda x: (x == "x", int(x) if x != "x" else 0)); tot = node["n"]; acc = 0; out = []
            for r in rs:
                n, nok = node["r"][r]; acc += n; out.append((acc / tot, None if r == "x" else int(r), nok / n))
            s.cache[key] = out
        return s.cache[key]

    def _find(s, table, keys, nmin=N_MIN):
        last = None
        for k in keys:
            v = table.get(k)
            if v is None: continue
            n = v["n"] if isinstance(v, dict) else v[1]
            if n >= nmin: return k, v
            last = last or (k, v)
        return last

    def cont_node(s, m, f, temp, k, e, prev):
        keys = []
        for kk in range(k, -1, -1):
            for ee in ((e, 0) if e else (0,)):
                keys += [f"{m}|{f}|{temp}|{kk}|{ee}|{prev}", f"{m}|{f}|{temp}|{kk}|{ee}|-",
                         f"*|{f}|{temp}|{kk}|{ee}|{prev}", f"*|{f}|{temp}|{kk}|{ee}|-", f"*|*|{temp}|{kk}|{ee}|-"]
        return s._find(s.cont, keys)

    def restart_node(s, m, f, k, e):
        keys = []
        for kk in range(max(1, k), 0, -1):
            for ee in ((e, 0) if e else (0,)):
                keys += [f"{m}|{f}|{kk}|{ee}", f"*|{f}|{kk}|{ee}", f"*|*|{kk}|{ee}"]
        return s._find(s.rst, keys)

    def draw(s, found, u_r, u_ok, done=0):
        """(further calls or None = no answer, right?) by inverse CDF: common random numbers across candidates. done > 0:
        the attempt is known to be unanswered after `done` calls (only outcomes r > done are kept; r is returned minus done)."""
        key, node = found; cdf = s._cdf(key, node)
        if done:
            keep = []; prev = 0.0
            for c, r, pok in cdf:
                if r is None or r > done: keep.append((c - prev, r, pok))
                prev = c
            tot = sum(x[0] for x in keep)
            if not keep or tot <= 0: return None, False
            acc = 0.0; cdf = []
            for m, r, pok in keep: acc += m / tot; cdf.append((acc, None if r is None else r - done, pok))
        for c, r, pok in cdf:
            if u_r <= c: return r, (r is not None and u_ok < pok)
        _, r, pok = cdf[-1]; return r, (r is not None and u_ok < pok)

    def restart_supported(s, m, f, k, e):
        """The record SAYS a restart beats continuing ReAct at this state: on the same tasks (paired), restart right & ReAct
        wrong outnumbers the reverse with one-sided exact sign-test p <= ALPHA (on the node the fork itself reads)."""
        hit = s.restart_node(m, f, k, e)
        if hit is None: return False
        nb, nw = hit[1]["pair"]; n = nb + nw
        return n > 0 and sum(math.comb(n, i) for i in range(nb, n + 1)) / 2 ** n <= ALPHA

    def q_ans(s, m, f, temp, c, e, prev):
        keys = []
        for cc in range(c, 0, -1):
            keys += [f"{m}|{f}|{temp}|{cc}|{e}|{prev}", f"{m}|{f}|{temp}|{cc}|{e}|-", f"*|{f}|{temp}|{cc}|{e}|{prev}",
                     f"*|{f}|{temp}|{cc}|{e}|-", f"*|*|{temp}|{cc}|{e}|-"]
        hit = s._find(s.ansd, keys)
        if hit is None: return 0.8
        nok, n = hit[1]; return (nok + 1) / (n + 2)

    def w_collide(s, m, f):
        hit = s._find(s.coll, [f"{m}|{f}", f"*|{f}", "*|*"], nmin=10)
        return (hit[1][0] + 1) / (hit[1][1] + 2) if hit else 0.2

    def tok_ag(s, m, f):
        t = s.tok.get(f"{m}|{f}") or s.tok["*|*"]; return t["a"], max(0.0, t["g"])


def prev_tag(lower, temp):
    """prev of a branch from the latent outcomes of the lower branches [(temp, answered, right)]; variant p = the paired
    record (one temperature-0 ReAct attempt before a temperature-0.7 attempt), else w = within the self-consistency record."""
    nc = sum(1 for t, a, ok in lower if a and ok); nw = sum(1 for t, a, ok in lower if a and not ok)
    v = "p" if (temp == "0.7" and len(lower) == 1 and lower[0][0] == "0") else "w"
    return f"{v}c{min(nc, 2)}w{min(nw, 2)}"

def tkey(temp): return "0" if temp == 0 else "0.7"


class AIAgents:
    horizon = 14
    samples = 64

    def __init__(s, spec="mock:0", standard="react", n_tasks=4):
        assert standard in ("react", "selfcons", "strongest")
        s.spec, s.standard, s.n_tasks = spec, standard, n_tasks
        s.mock = spec.startswith("mock")
        if not s.mock: llm.NATIVE_TOOLS = True                # design v3: tools declared natively
        s.tree = Tree(); s.mk = s.tree.model_key(spec); s.post_cache = {}; s.cges_cache = {}

    def _t0(s): return 0.0 if s.standard == "react" else 0.7

    # ---------- episode ----------
    def tasks_for(s, cell):
        base = 7_000_000 + 10 * cell
        return [make(f, [base + k])[0] for k, f in enumerate(["staff", "orders", "staff", "orders"][:s.n_tasks])]

    def _branch(s, task, b, temp):
        return {"id": b, "temp": temp, "msgs": [{"role": "user", "content": "Task: " + task["question"]}], "answer": None,
                "calls": 0, "tok": 0, "first_tok": 0, "last_tok": 0, "growth": 0, "errors": 0, "fmt": 0, "restarts": 0}

    def reset(s, cell):
        s.post_cache = {}; s.cges_cache = {}
        tasks = s.tasks_for(cell)
        return {"sim": False, "cell": cell, "t": 0, "ti": 0, "tasks": tasks, "br": [s._branch(tasks[0], 0, s._t0())],
                "calls": 0, "tok": 0, "tok_total": 0, "votes_done": [], "correct": [], "done_est": 0.0,
                "errors": [], "failed_calls": 0, "usage_est": 0, "text_toolcalls": 0, "withheld_tasks": 0}

    def done(s, st):
        if st["sim"]: return st["ti"] > st["ti0"] or st["ti"] >= s.n_tasks
        return st["ti"] >= s.n_tasks

    # ---------- standard method (unchanged) ----------
    def default(s, st):
        br = st["br"]
        if s.standard == "react":
            return ("step", 0) if br[0]["answer"] is None else ("commit",)
        last = br[-1]                                          # selfcons: sequential attempts, then majority
        if last["answer"] is None: return ("step", last["id"])
        if s.standard == "strongest" and s._cges_top(st) >= GAMMA: return ("commit",)   # CGES / ReASC early stop
        if len(br) < 3: return ("new",)
        return ("commit",)

    # ---------- strongest: CGES posterior over the given answers (calibrated reliability, no log-probs) ----------
    def _fam(s, st): return st["fam"] if st["sim"] else st["tasks"][st["ti"]]["family"]

    def _ans_items(s, st):
        out = []
        for b in st["br"]:
            if b["answer"] is None: continue
            e = b["e"] if st["sim"] else int(b["errors"] + b["fmt"] > 0)
            out.append((b["answer"], ("B" if b.get("kind") == "blind" else "") + tkey(b["temp"]), b["calls"], e))
        return tuple(out)

    def _cges(s, fam, items):
        """{answer: posterior} over the given answers (CGES Eq.; K = distinct answers + 1 unseen), and the top value."""
        key = (fam, items)
        if key in s.cges_cache: return s.cges_cache[key]
        cands = list(dict.fromkeys(a for a, _, _, _ in items)); K = len(cands) + 1
        C = [min(0.999, max(0.001, s.p_blind(fam, tp[1:], "-") if tp.startswith("B") else s.tree.q_ans(s.mk, fam, tp, c, e, "-")))
             for _, tp, c, e in items]
        sc = {}
        for h in cands + [None]:
            p = 1.0
            for (a, _, _, _), ct in zip(items, C): p *= ct if a == h else (1 - ct) / (K - 1)
            sc[h] = p
        z = sum(sc.values()) or 1.0; post = {h: v / z for h, v in sc.items()}
        out = (post, max(post.values())); s.cges_cache[key] = out; return out

    def _cges_top(s, st):
        items = s._ans_items(st)
        return s._cges(s._fam(st), items)[1] if items else 0.0

    def _final(s, st):
        """The committed answer: majority (react, selfcons; Counter order) or the CGES posterior argmax (strongest)."""
        votes = [b["answer"] for b in st["br"] if b["answer"] is not None]
        if not votes: return None
        if s.standard != "strongest": return majority(votes)
        post = s._cges(s._fam(st), s._ans_items(st))[0]; order = [a for a, _ in collections.Counter(votes).most_common()]
        return max(order, key=lambda a: (post[a], -order.index(a)))

    def branches(s, st):
        br = st["br"]; d = s.default(st); out = []
        if s.standard == "react" and not s._can_restart(st, br[0]):
            return []    # 24 Nov: deviate from ReAct only where the paired record says its current attempt tends to fail
        unans = [b["id"] for b in br if b["answer"] is None]; ans = [b["id"] for b in br if b["answer"] is not None]
        for b in unans:
            if ("step", b) != d: out.append((f"focus-b{b}", ("step", b)))
        for b in unans:
            if s._can_restart(st, br[b]): out.append((f"restart-b{b}", ("restart", b)))
        if len(br) < 3 and d != ("new",): out.append(("open", ("new",)))
        if ans and d != ("commit",): out.append(("stop", ("commit",)))
        if ans and unans: out.append(("cross", ("cross", unans[0], ans[0])))          # coupled: one branch drives another
        return out[:6]

    def _can_restart(s, st, b):
        """Only what the tree records: a temperature-0 ReAct attempt, unanswered after >= 1 call, restarted at most once, at a
        state where the paired record favours the restart (Tree.restart_supported)."""
        if not (b["answer"] is None and b["calls"] >= 1 and b["temp"] == 0 and not b.get("rs")): return False
        if b.get("kind") == "blind" or b.get("conv"): return False                    # REAL3: blind / converted branches
        e = b["e"] if st["sim"] else int(b["errors"] + b["fmt"] > 0)
        fam = st["fam"] if st["sim"] else st["tasks"][st["ti"]]["family"]
        return s.tree.restart_supported(s.mk, fam, b["calls"], e)

    def _budget_ok(s, st): return st["calls"] + 1 <= MAX_CALLS and st["tok"] < MAX_TOK

    def valid(s, st, a):
        a = tuple(a) if a else ("commit",); br = st["br"]; ids = {b["id"]: b for b in br}
        if not s._budget_ok(st): return ("commit",)
        k = a[0]
        if k == "commit":
            return a if any(b["answer"] is not None for b in br) else s.default(st)
        if k == "withhold":   # REAL2 landing: the call withheld; with an answer in hand that is a plain commit
            return ("commit",) if any(b["answer"] is not None for b in br) else ("withhold",)
        if k == "new":
            return a if len(br) < 3 else s.default(st)
        if k == "step":
            return a if len(a) == 2 and a[1] in ids and ids[a[1]]["answer"] is None else s.default(st)
        if k == "restart":
            return a if (len(a) == 2 and a[1] in ids and s._can_restart(st, ids[a[1]])) else s.default(st)
        if k in ("blind", "reuse"):                                      # REAL3 frame actions
            return a if (len(a) == 2 and s._blind_ok(st, a[1], k == "reuse")) else s.default(st)
        if k == "cross" and len(a) == 3 and a[1] in ids and ids[a[1]].get("kind") == "blind":
            return ("step", a[1]) if ids[a[1]]["answer"] is None else s.default(st)
        if k == "cross":
            ok = (len(a) == 3 and a[1] in ids and a[2] in ids and ids[a[1]]["answer"] is None and ids[a[2]]["answer"] is not None)
            return a if ok else s.default(st)
        return s.default(st)

    # ---------- real transition ----------
    def step(s, st, a):
        if st["sim"]: return s._sim_step(st, a)
        st = dict(st); st["br"] = list(st["br"]); st["t"] += 1
        task = st["tasks"][st["ti"]]
        if a[0] in ("commit", "withhold"):
            votes = [norm(b["answer"]) for b in st["br"] if b["answer"] is not None]
            final = s._final(st)
            st["done_est"] = st["done_est"] + s._p_majority(st)
            st["votes_done"] = st["votes_done"] + [votes]
            st["correct"] = st["correct"] + [bool(correct(task, None if final is None else norm(final)))]
            st["withheld_tasks"] += a[0] == "withhold"
            s._pool_update(st, task, final)
            st["ti"] += 1; st["calls"] = 0; st["tok"] = 0
            if st["ti"] < s.n_tasks:
                st["br"] = [s._branch(st["tasks"][st["ti"]], 0, s._t0())]
            return st
        if a[0] in ("blind", "reuse") or (a[0] == "step" and st["br"][a[1]].get("kind") == "blind"):
            return s._blind_step(st, task, a)
        hint = None
        if a[0] == "new":
            b = s._branch(task, len(st["br"]), 0.7); st["br"].append(b); bi = b["id"]
        elif a[0] == "restart":
            bi = a[1]; old = st["br"][bi]; b = s._branch(task, bi, 0.7); b["restarts"] = old["restarts"] + 1
            b["rs"] = (old["calls"], int(old["errors"] + old["fmt"] > 0)); st["br"][bi] = b
        else:
            bi = a[1]
            if a[0] == "cross":
                hint = ("Another independent attempt answered: " + str(st["br"][a[2]]["answer"]) +
                        ". Check it against your own tool results, then continue with ACTION or ANSWER.")
        b = dict(st["br"][bi]); b["msgs"] = list(b["msgs"])
        if hint:   # an unanswered branch always ends on a user turn (task, observation or format note): append the hint to it
            b["msgs"][-1] = {"role": "user", "content": b["msgs"][-1]["content"] + "\n" + hint}
        res = s._mock_call(st, task, b) if s.mock else s._chat(st, task, b)
        if res is None:      # the call failed twice (logged): close this task's budget; the task commits next step
            st["failed_calls"] += 1; st["calls"] = MAX_CALLS; st["br"][bi] = b
            return st
        txt, ti_, to_ = res
        used = ti_ + to_
        b["growth"] = used - b["last_tok"] if b["calls"] else 0; b["last_tok"] = used
        if not b["calls"]: b["first_tok"] = used
        b["calls"] += 1; b["tok"] += used; st["calls"] += 1; st["tok"] += used; st["tok_total"] += used
        b["msgs"].append({"role": "assistant", "content": txt})
        m_ans = last_line(txt, ANS); m_act = last_line(txt, ACT)
        if m_ans and not m_act:
            b["answer"] = norm(m_ans.group(1))
        elif m_act:
            obs = run_tool(task, m_act.group(1), m_act.group(2).strip())
            if str(obs).startswith("error"): b["errors"] += 1
            b["msgs"].append({"role": "user", "content": "Observation: " + str(obs)})
        else:
            b["fmt"] += 1
            b["msgs"].append({"role": "user", "content": "Reply must end with one line: ACTION: tool(arguments) or ANSWER: value"})
        st["br"][bi] = b
        return st

    def _chat(s, st, task, b):
        """One real model call, robust (24 Nov): exception text logged per cell, ONE retry (empty assistant turns sent as
        "(no reply)" on the retry), None after a second failure. Missing usage -> chars/4 estimate. Text tool calls ->
        text actions (normalise_reply). Never raises on a model / provider error."""
        system = system_prompt(task); msgs = b["msgs"]
        for k in range(2):
            if k:
                msgs = [{"role": m["role"], "content": m["content"] if (m["content"] or "").strip() else "(no reply)"}
                        for m in msgs]
            try:
                txt, ti_, to_ = LB.chat(s.spec, system, msgs, max_tokens=REPLY_TOK, temperature=b["temp"], tools=task["tools"])
                break
            except Exception as e:     # noqa: BLE001  (log, retry once if worthwhile, never crash the episode)
                body = str(getattr(e, "body", "") or "")[:300].replace("\n", " ")
                note = (f"[ai_agents {s.spec} std={s.standard} cell {st['cell']} task {st['ti']} branch {b['id']} "
                        f"call {b['calls'] + 1} try {k + 1}/2] {type(e).__name__}: {str(e)[:300]}" + (f" | body: {body}" if body else ""))
                st["errors"] = st["errors"] + [note]; print(note, file=sys.stderr, flush=True)
                if not LB.retry_worthwhile(e): return None
        else:
            return None
        txt = txt if isinstance(txt, str) else str(txt or "")
        ti_, to_ = int(ti_ or 0), int(to_ or 0)
        if ti_ + to_ == 0:             # usage missing: estimate so the token budget still binds (counted)
            ti_ = math.ceil((len(system) + sum(len(m["content"] or "") for m in msgs)) / 4); to_ = math.ceil(len(txt) / 4)
            st["usage_est"] += 1
        txt, rw = normalise_reply(txt, task["tools"]); st["text_toolcalls"] += rw
        return txt, ti_, to_

    def _mock_call(s, st, task, b):
        """STAND-IN for the interface check only, never for results: a deterministic scripted model."""
        extra = [b["restarts"]] if b.get("restarts") else []   # a restarted attempt is a fresh draw; no restart = as before
        need = 2 + int(np.random.default_rng([st["cell"], st["ti"], b["id"], 5502] + extra).integers(0, 4))
        r = np.random.default_rng([st["cell"], st["ti"], b["id"], b["calls"], 5501] + extra)
        tin, tout = 380 + 160 * b["calls"], 110
        if b["calls"] + 1 < need:
            tool = task["tools"][0]; arg = "dept=Sales" if tool == "filter" else "product=lamp"
            return f"Thought: gather data.\nACTION: {tool}({arg})", tin, tout
        p = 0.82 if b["temp"] == 0 else 0.75
        ans = task["answer"]
        if r.random() >= p:
            ans = (ans + int(r.integers(1, 50))) if isinstance(ans, int) else NAMES[int(r.integers(0, len(NAMES)))]
        return f"Thought: done.\nANSWER: {ans}", tin, tout

    # ---------- the host's own model: the real tree ----------
    def _posterior(s, st):
        """[(probability, right answer string or None)] over the answered branches' distinct answers (tree ans + collide)."""
        fam = st["tasks"][st["ti"]]["family"]
        ansd = [b for b in st["br"] if b["answer"] is not None]
        key = (st["cell"], st["ti"], tuple((b["id"], b["answer"], b["temp"], b["calls"], b["errors"] + b["fmt"], b.get("kind"))
                                           for b in ansd))
        if key in s.post_cache: return s.post_cache[key]
        w = s.tree.w_collide(s.mk, fam); hyps = []
        for h in list(dict.fromkeys(b["answer"] for b in ansd)) + [None]:
            like = 1.0; lower = []; wrongs = []
            for b in ansd:
                tp = tkey(b["temp"])
                q = (s.p_blind(fam, tp, prev_tag(lower, tp)) if b.get("kind") == "blind" else
                     s.tree.q_ans(s.mk, fam, tp, b["calls"], int(b["errors"] + b["fmt"] > 0), prev_tag(lower, tp)))
                if b["answer"] == h: like *= q; lower.append((tp, True, True))
                else:
                    like *= (1 - q) * ((w / len(set(wrongs)) if b["answer"] in wrongs else 1 - w) if wrongs else 1.0)
                    wrongs.append(b["answer"]); lower.append((tp, True, False))
            hyps.append([like, h])
        z = sum(x[0] for x in hyps) or 1.0
        out = [(x[0] / z, x[1]) for x in hyps]; s.post_cache[key] = out; return out

    def _p_majority(s, st):
        """P(the committed answer is right) under the tree posterior (majority, or the CGES argmax under strongest)."""
        mj = s._final(st)
        if mj is None: return 0.0
        return sum(p for p, h in s._posterior(st) if h == mj)

    def fork(s, st, j):
        if st["sim"]: raise ValueError("fork of a fork")
        r = np.random.default_rng([st["cell"], st["t"], j, 7331])
        U = r.random((1, 3, 3))      # slot 0..2 x (u_r, u_ok, u_collide); a restart reads the same uniforms (coupled draws)
        u_h = r.random()
        V = r.random((3, 4))         # REAL3: plan-execution uniforms per slot (drawn after every REAL1/REAL2 draw)
        fam = st["tasks"][st["ti"]]["family"]; a_tok, g = s.tree.tok_ag(s.mk, fam)
        acc = 0.0; right = None
        for p, h in s._posterior(st):
            acc += p
            if u_h <= acc: right = h; break
        right = right if right is not None else ("right",)              # the right answer nobody has given yet
        first = next((b["first_tok"] for b in st["br"] if b["calls"] and b.get("kind") != "blind"), a_tok)
        sb = []; lower = []
        for b in st["br"]:
            tp = tkey(b["temp"]); e = int(b["errors"] + b["fmt"] > 0); costs = []
            if b["answer"] is not None:
                ok = b["answer"] == right; left = 0; lower.append((tp, True, ok))
            elif b.get("kind") == "blind":   # REAL3: a blind branch waiting for a re-plan (hologram context)
                hit = (s.tree.restart_node(s.mk, fam, *b["bconv"]) if b.get("bconv") else
                       s.tree.cont_node(s.mk, fam, tp, 0, 0, prev_tag(lower, tp)))
                r0, ok = s.tree.draw(hit, *U[0, b["id"], :2])
                left, costs = s._blind_draw(fam, V[b["id"]], BL.MAX_RETRY + 1 - b["fails"], r0, replan=True)
                lower.append((tp, left is not None, ok))
            elif b.get("rs"):    # a restarted attempt: the restart record, given it is still unanswered after its calls
                left, ok = s.tree.draw(s.tree.restart_node(s.mk, fam, *b["rs"]), *U[0, b["id"], :2], done=b["calls"])
                lower.append((tp, left is not None, ok))
            else:
                left, ok = s.tree.draw(s.tree.cont_node(s.mk, fam, tp, b["calls"], e, prev_tag(lower, tp)), *U[0, b["id"], :2])
                lower.append((tp, left is not None, ok))
            sb.append({"id": b["id"], "temp": b["temp"], "answer": b["answer"], "calls": b["calls"], "e": e, "left": left,
                       "rs": b.get("rs"), **({"kind": "blind", "costs": costs} if b.get("kind") == "blind" else {}),
                       **({"conv": True} if b.get("conv") else {}),
                       "ok": ok, "next": (b["last_tok"] + g) if b["calls"] else first})
            if b.get("kind") == "blind": sb[-1]["next"] = first
        new_out = {}
        for i in range(len(st["br"]), 3):                                  # branches that do not exist yet
            left, ok = s.tree.draw(s.tree.cont_node(s.mk, fam, "0.7", 0, 0, prev_tag(lower, "0.7")), *U[0, i, :2])
            new_out[i] = (left, ok); lower.append(("0.7", left is not None, ok))
        return {"sim": True, "cell": st["cell"], "t": st["t"], "ti": st["ti"], "ti0": st["ti"], "fam": fam, "U": U, "g": g,
                "first": first, "right": right, "br": sb, "new_out": new_out, "calls": st["calls"], "tok": st["tok"],
                "tok_total": st["tok_total"], "done_est": st["done_est"], "V": V,
                "reuse_pr": s._reuse_pr(st), "reused": st.get("reused_task", False)}

    def _sim_step(s, f, a):
        f = dict(f); f["br"] = [dict(b) for b in f["br"]]; f["t"] += 1
        if a[0] in ("commit", "withhold"):
            f["done_est"] = f["done_est"] + s._sim_right(f); f["ti"] += 1; return f
        if a[0] == "new":
            i = len(f["br"]); left, ok = f["new_out"][i]
            f["br"].append({"id": i, "temp": 0.7, "answer": None, "calls": 0, "e": 0, "left": left, "ok": ok, "next": f["first"]})
            b = f["br"][-1]
        elif a[0] in ("blind", "reuse"):
            return s._sim_blind(f, a)
        elif a[0] == "restart":
            b = f["br"][a[1]]
            left, ok = s.tree.draw(s.tree.restart_node(s.mk, f["fam"], b["calls"], b["e"]), *f["U"][0, b["id"], :2])
            b.update({"temp": 0.7, "calls": 0, "e": 0, "left": left, "ok": ok, "next": f["first"], "rs": (b["calls"], b["e"])})
        else:
            b = f["br"][a[1]]                                              # step or cross (the hint is not in the record)
        if b.get("costs"):                                                 # REAL3: a plan call (fixed size, no transcript)
            c = b["costs"].pop(0); f["tok"] += c; f["tok_total"] += c; f["calls"] += 1; b["calls"] += 1
        else:
            f["tok"] += b["next"]; f["tok_total"] += b["next"]; f["calls"] += 1; b["next"] += f["g"]; b["calls"] += 1
        if b["left"] is not None:
            b["left"] -= 1
            if b["left"] <= 0:
                if b["ok"]: b["answer"] = f["right"]
                else:
                    wrong = [x["answer"] for x in f["br"] if x["answer"] is not None and x["answer"] != f["right"]]
                    collide = wrong and f["U"][0, b["id"], 2] < s.tree.w_collide(s.mk, f["fam"])
                    b["answer"] = majority(wrong) if collide else ("wrong", f["t"], b["id"])
        return f

    def _sim_right(s, f):
        fin = s._final(f)
        return 1.0 if fin is not None and fin == f["right"] else 0.0

    # ---------- REAL2 A: Law 4 landings (one model call on one reasoning branch) ----------
    def landings(s, st, a):
        a = tuple(a)
        if a[0] in ("step", "cross", "restart"): return [("call", a[1])]
        if a[0] == "new": return [("call", len(st["br"]))]
        if a[0] == "blind": return [("call", a[1])]                     # REAL3: one plan call; a reuse makes no call
        return []                                                       # commit / withhold: no call, no landing

    def without(s, st, a, L):
        return ("commit",) if any(b["answer"] is not None for b in st["br"]) else ("withhold",)

    def _need(s, st, T):
        """The tree's P(this attempt ends with a right answer | its state) for a placement T of the call."""
        fam = s._fam(st); br = st["br"]
        if T[0] == "new": hit = s.tree.cont_node(s.mk, fam, "0.7", 0, 0, "-")
        elif T[0] == "restart":
            b = br[T[1]]; hit = s.tree.restart_node(s.mk, fam, b["calls"], int(b["errors"] + b["fmt"] > 0))
        else:
            b = br[T[1]]; hit = s.tree.cont_node(s.mk, fam, tkey(b["temp"]), b["calls"], int(b["errors"] + b["fmt"] > 0), "-")
        if not hit: return 0.0
        node = hit[1]; return sum(x[1] for x in node["r"].values()) / node["n"]

    def targets(s, st, a, L):
        br = st["br"]
        if s.standard == "react" and not s._can_restart(st, br[0]): return []   # same gate as branches()
        cur = s.valid(st, a); out = []
        for b in br:
            if b["answer"] is None and ("step", b["id"]) != cur and b["id"] != L[1]: out.append(("step", b["id"]))
        if len(br) < 3 and cur != ("new",): out.append(("new",))
        for b in br:
            if b["answer"] is None and s._can_restart(st, b) and ("restart", b["id"]) != cur: out.append(("restart", b["id"]))
        out = [T for T in out if s.valid(st, T) == T]
        return sorted(out, key=lambda T: -s._need(st, T))[:3]

    def retarget(s, st, a, L, T): return tuple(T)

    # ---------- REAL3: library primitives, frame levers, coupling (seed3 interface) ----------
    def primitives(s, st):
        """P4P5 = the strongest method's action here (CGES / ReASC posterior stop, else the next attempt); P8 = a vote of
        futures (one more attempt) when an answer is in hand."""
        br = st["br"]; out = []; last = br[-1]
        if last["answer"] is None: a = ("step", last["id"])
        elif s._cges_top(st) >= GAMMA or len(br) >= 3: a = ("commit",)
        else: a = ("new",)
        out.append(("P4P5", "P4P5-cges", a))
        if len(br) < 3 and any(b["answer"] is not None for b in br): out.append(("P8", "P8-vote", ("new",)))
        return out

    def frame(s, st):
        """F:blind (one plan call; the runtime computes), F:reuse (a pooled plan of this question's shape, no call),
        F:vote (stop where the tree is sure, one more attempt only where it is uncertain). Hologram context is inside every
        re-plan call of a blind branch."""
        br = st["br"]; out = []
        slot = next((b["id"] for b in br if s._blind_ok(st, b["id"], False)), None)
        if slot is None and len(br) < 3 and all(b["answer"] is not None for b in br): slot = len(br)
        if slot is not None:
            out.append(("F:blind", f"F:blind-b{slot}", ("blind", slot)))
            if s._blind_ok(st, slot, True): out.append(("F:reuse", f"F:reuse-b{slot}", ("reuse", slot)))
        if any(b["answer"] is not None for b in br) and all(b["answer"] is not None for b in br):
            top = max(p for p, h in s._posterior(st) if h is not None)
            if top >= GAMMA: out.append(("F:vote", "F:vote-stop", ("commit",)))
            elif len(br) < 3: out.append(("F:vote", "F:vote-open", ("new",)))
        return out

    def coupled(s, st):
        """The branches drive each other once an answer is in hand: the committed answer is their joint vote."""
        return len(st["br"]) >= 2 and any(b["answer"] is not None for b in st["br"])

    # ---------- REAL3: blind planning (real step) ----------
    def _blind_ok(s, st, i, reuse):
        br = st["br"]
        if reuse:
            if st.get("reused_task") if not st["sim"] else st["reused"]: return False
            if (st["reuse_pr"] if st["sim"] else s._reuse_pr(st)) is None: return False
        if i == len(br): return len(br) < 3
        if not (0 <= i < len(br)): return False
        b = br[i]
        return (b["answer"] is None and b.get("kind") != "blind" and not b.get("conv") and
                (b["calls"] == 0 or s._can_restart(st, b)))

    def _reuse_pr(s, st):
        if st["sim"]: return st["reuse_pr"]
        task = st["tasks"][st["ti"]]; key, _ = BL.pool_match(s.spec, task["family"], task["question"])
        if key is None: return None
        e = BL.PLAN_POOL[key]; return (e["exec_ok"] + 3) / (e["uses"] + 4)

    def _blind_step(s, st, task, a):
        st = dict(st); br = st["br"] = list(st["br"]); st["t"] += 1; i = a[1]
        if a[0] in ("blind", "reuse"):
            if i == len(br): nb = s._branch(task, i, 0.7); br.append(nb)
            else:
                old = br[i]; nb = s._branch(task, i, old["temp"]); nb["restarts"] = old["restarts"]
                if old["calls"]: nb["bconv"] = (old["calls"], int(old["errors"] + old["fmt"] > 0))
            nb.update({"kind": "blind", "conv": True, "fails": 0, "plan_calls": 0, "last_plan": None, "fb": None})
            if a[0] == "reuse":
                st["reused_task"] = True
                key, plan = BL.pool_match(s.spec, task["family"], task["question"]); e = BL.PLAN_POOL[key]; e["uses"] += 1
                nb["reuse_key"] = key
                if s._exec(st, task, nb, plan, call=False): e["exec_ok"] += 1; st["plans_reused"] = st.get("plans_reused", 0) + 1
                br[i] = nb; return st
        else:
            nb = dict(br[i])
        msg = ("Task: " + task["question"]) if nb["fb"] is None else BL.replan_message(task, nb["last_plan"], *nb["fb"])
        res = s._mock_plan_call(st, task, nb) if s.mock else s._plan_chat(st, task, nb, msg)
        if res is None:
            st["failed_calls"] += 1; st["calls"] = MAX_CALLS; br[i] = nb; return st
        txt, ti_, to_ = res; used = ti_ + to_; kind = "replan" if nb["fb"] is not None else "plan"
        nb["calls"] += 1; nb["plan_calls"] += 1; nb["tok"] += used
        st["calls"] += 1; st["tok"] += used; st["tok_total"] += used; st["plan_calls"] = st.get("plan_calls", 0) + 1
        t = BL.TRACE.setdefault((s.spec, task["family"], kind), [0, 0]); t[0] += used; t[1] += 1
        s._exec(st, task, nb, txt, call=True)
        br[i] = nb; return st

    def _exec(s, st, task, nb, text, call):
        """Parse and run the plan (0 calls). Failure -> feedback for a hologram re-plan; after MAX_RETRY re-plans the branch
        falls back to a fresh ReAct attempt (its plan calls stay counted)."""
        plan = (text or "")[:600]
        try:
            ops, ans = BL.parse(text); plan = BL.render(ops, ans)
            v, notes, dg = BL.Runtime(task).run(ops, ans)
            if notes and plan != nb["last_plan"]:
                raise BL.PlanError("; ".join(notes) + " (if that is intended, repeat the plan unchanged)") from None
            nb["answer"] = norm(v); nb["plan_ok"] = plan; st["blind_answers"] = st.get("blind_answers", 0) + 1
            if call: x = BL.EXEC.setdefault((s.spec, task["family"]), [0, 0]); x[0] += 1; x[1] += 1
            return True
        except BL.PlanError as e:
            nb["last_plan"] = plan; nb["fb"] = (str(e), list(getattr(e, "digest", None) or []))
            if not call: return False
            nb["fails"] += 1; st["plan_failures"] = st.get("plan_failures", 0) + 1
            x = BL.EXEC.setdefault((s.spec, task["family"]), [0, 0]); x[1] += 1
            if nb["fails"] >= BL.MAX_RETRY + 1:                            # fallback: a fresh ReAct attempt in this slot
                nb.update({"kind": "react", "msgs": [{"role": "user", "content": "Task: " + task["question"]}], "calls": 0,
                           "last_tok": 0, "first_tok": 0, "growth": 0, "errors": 0, "fmt": 0})
                nb.pop("bconv", None); st["blind_fallbacks"] = st.get("blind_fallbacks", 0) + 1
            return False

    def _pool_update(s, st, task, final):
        """O-trace: a plan whose answer is the committed answer is confirmed (stored under its shape); one whose answer
        differs is contradicted (removed when contradicted more often than confirmed). No ground truth."""
        if st["sim"] or final is None: return
        for b in st["br"]:
            if b.get("kind") != "blind" or not b.get("plan_ok"): continue
            conf = norm(b["answer"]) == norm(final); key = b.get("reuse_key")
            if key in BL.PLAN_POOL:
                e = BL.PLAN_POOL[key]; e["agree" if conf else "disagree"] += 1
                if e["disagree"] > e["agree"]: del BL.PLAN_POOL[key]
            elif key is None:
                BL.pool_record(s.spec, task["family"], task["question"], b["plan_ok"], conf)

    def _plan_chat(s, st, task, b, msg):
        """One real planner call (no tools declared: the plan is text). Robust like _chat: one retry, None after two failures."""
        system = BL.system_prompt(task)
        for k in range(2):
            try:
                txt, ti_, to_ = LB.chat(s.spec, system, [{"role": "user", "content": msg}], max_tokens=REPLY_TOK,
                                        temperature=b["temp"], tools=None)
                break
            except Exception as e:     # noqa: BLE001
                note = (f"[ai_agents {s.spec} std={s.standard} cell {st['cell']} task {st['ti']} blind branch {b['id']} "
                        f"plan call {b['plan_calls'] + 1} try {k + 1}/2] {type(e).__name__}: {str(e)[:300]}")
                st["errors"] = st["errors"] + [note]; print(note, file=sys.stderr, flush=True)
                if not LB.retry_worthwhile(e): return None
        else:
            return None
        txt = txt if isinstance(txt, str) else str(txt or ""); ti_, to_ = int(ti_ or 0), int(to_ or 0)
        if ti_ + to_ == 0:
            ti_ = math.ceil((len(system) + len(msg)) / 4); to_ = math.ceil(len(txt) / 4); st["usage_est"] += 1
        return txt, ti_, to_

    def _mock_plan_call(s, st, task, b):
        """STAND-IN for the interface check only, never for results: a scripted planner (ai_agents_blind.mock_plan)."""
        r = np.random.default_rng([st["cell"], st["ti"], b["id"], b["plan_calls"], 5503])
        txt = BL.mock_plan(task, r, 0.82 if b["temp"] == 0 else 0.75)
        return txt, 600 + (300 if b["fb"] is not None else 0), 30 + len(txt) // 4

    # ---------- REAL3: blind planning in the host's own model (forks) ----------
    def p_blind(s, fam, tp, prev):
        """P(right | answered) of a FRESH attempt of this model at this temperature (tree node k = 0): the blind plan is
        valued as exactly as accurate as a fresh attempt (no accuracy gain assumed; no blind record exists yet)."""
        key = ("pb", fam, tp, prev)
        if key not in s.post_cache:
            hit = s.tree.cont_node(s.mk, fam, tp, 0, 0, prev); n = nok = 0
            for r, (nn, kk) in (hit[1]["r"].items() if hit else []):
                if r != "x": n += nn; nok += kk
            s.post_cache[key] = (nok + 1) / (n + 2)
        return s.post_cache[key]

    def _pe(s, fam):
        """P(a plan call executes without a detected failure): this host's O-trace, prior Beta(3, 1) (A7 X5b: 4 invalid
        step outputs in 32 tasks, every one repaired within the task)."""
        ok, n = BL.EXEC.get((s.spec, fam), (0, 0)); return (ok + 3) / (n + 4)

    def _ptok(s, fam, kind):
        """Tokens of a plan / re-plan call: this host's O-trace mean (>= 3 calls), else the tree's first-call size + 250
        (plan) / + 400 (re-plan with the digest): a stated prior."""
        tot, n = BL.TRACE.get((s.spec, fam, kind), (0, 0))
        if n >= 3: return tot / n
        return s.tree.tok_ag(s.mk, fam)[0] + (250 if kind == "plan" else 400)

    def _blind_draw(s, fam, v, tries, r_react, replan):
        """(further calls until the blind branch answers or None, per-call token costs). Exec success per call ~ pe; after
        `tries` failed calls the fallback ReAct attempt answers after r_react more calls (tree draw, coupled uniforms)."""
        pe = s._pe(fam); costs = []
        for j in range(max(0, tries)):
            costs.append(s._ptok(fam, "replan" if (replan or j) else "plan"))
            if v[j] < pe: return j + 1, costs
        return (None if r_react is None else len(costs) + r_react), costs

    def _sim_blind(s, f, a):
        br = f["br"]; i = a[1]; fam = f["fam"]
        if i == len(br):
            left0, ok = f["new_out"][i]
            b = {"id": i, "temp": 0.7, "answer": None, "calls": 0, "e": 0, "next": f["first"]}; br.append(b)
        else:
            b = br[i]
            if b["calls"] == 0: left0, ok = b["left"], b["ok"]
            else: left0, ok = s.tree.draw(s.tree.restart_node(s.mk, fam, b["calls"], b["e"]), *f["U"][0, i, :2])
            b.update({"calls": 0, "e": 0, "next": f["first"]})
        b.update({"kind": "blind", "conv": True, "ok": ok})
        if a[0] == "reuse":
            f["reused"] = True
            if f["V"][i, 3] < f["reuse_pr"]:                                  # the pooled plan runs: an answer at 0 calls
                b["left"] = None; b["answer"] = f["right"] if (ok and left0 is not None) else ("wrong", f["t"], i)
                return f
            b["left"], b["costs"] = s._blind_draw(fam, f["V"][i], BL.MAX_RETRY + 1, left0, replan=True)
            return f
        b["left"], b["costs"] = s._blind_draw(fam, f["V"][i], BL.MAX_RETRY + 1, left0, replan=False)
        return s._sim_step(f, ("step", i))

    # ---------- REAL3 v2: seed operator hooks (real/HOST_INTERFACE_REAL3v2.md) ----------
    # PARTS = the attempt slots of the current task (part id = (task index, slot)): the existing reasoning branches plus
    # the next empty slot while fewer than 3 exist. The step's resource is ONE model call (or none), and it lands on one
    # slot: that is the unit the landing step (REAL2) already uses. Tasks are not parts: a step can only act on the
    # current task (the 4 tasks are sequential), so a "task part" would have no action of its own.
    def _slot_of(s, st, a):
        a = tuple(a)
        if a[0] in ("step", "cross", "restart", "blind", "reuse") and len(a) >= 2: return a[1]
        if a[0] == "new": return len(st["br"])
        return None                                                     # commit / withhold: no call, no slot

    def parts(s, st):
        n = len(st["br"])
        return [(st["ti"], b) for b in range(n)] + ([(st["ti"], n)] if n < 3 else [])

    def merge(s, st, d):
        """One call per step: the first named part (dict order) whose action calls on that part's slot gets the call;
        parts not named take the standard. merge(s, {p: a}) = a if a's call lands on p, else the standard action."""
        for (ti, b), a in d.items():
            if a is not None and ti == st["ti"] and s._slot_of(st, a) == b: return tuple(a)
        return s.default(st)

    def part_objective(s, st, p):
        """The slot's own value now: P(it contributes a right answer) from the real tree. Answered branch: the posterior
        P(its answer is the right one); unanswered branch: P(this attempt ends with a right answer | its state) (restart /
        blind branches read the fresh node); empty slot: a fresh temperature-0.7 attempt."""
        ti, b = p; br = st["br"]
        if ti != st["ti"]: return 0.0
        if b < len(br) and br[b]["answer"] is not None:
            return float(sum(pp for pp, h in s._posterior(st) if h == br[b]["answer"]))
        if b >= len(br) or br[b].get("kind") == "blind" or br[b].get("rs"): return float(s._need(st, ("new",)))
        return float(s._need(st, ("step", b)))

    def focus(s, st, p):
        """The step's whole resource (its one call) on slot p: the next step of that branch, or a new attempt there."""
        ti, b = p; br = st["br"]
        if ti != st["ti"]: return s.default(st)
        if b == len(br) and len(br) < 3: return ("new",)
        if b < len(br) and br[b]["answer"] is None: return ("step", b)
        return s.default(st)

    def joint(s, st):
        """Native joint action: CROSS (one branch's next call told another branch's answer: two parts in one call)."""
        br = st["br"]; un = [b["id"] for b in br if b["answer"] is None and b.get("kind") != "blind"]
        an = [b["id"] for b in br if b["answer"] is not None]
        return [("cross", ("cross", un[0], an[0]))] if un and an else []

    def map_part(s, st, a, pf, pt):
        """The same operation re-expressed on another slot (step / restart / blind / reuse / cross of pt; a call on the
        empty slot = a new attempt). valid() turns what is not possible on pt into the standard."""
        a = tuple(a); bt = pt[1]; n = len(st["br"])
        if a[0] == "new" or bt == n:
            k = a[0] if a[0] in ("blind", "reuse") else "new"
            return (k, bt) if k != "new" else ("new",)
        if a[0] in ("step", "restart", "blind", "reuse"): return (a[0], bt)
        if a[0] == "cross": return ("cross", bt, a[2])
        return a

    def shape(s, st):
        """Compact state key (COMPRESS, INHERIT): standard, family, question type (its first words), per slot (kind,
        answered, calls <= 4, error), whether a pooled plan of this question's shape exists. Never a value or an answer."""
        task = st["tasks"][st["ti"]]; q = " ".join(task["question"].split()[:3])
        br = tuple(("B" if b.get("kind") == "blind" else "R") + ("a" if b["answer"] is not None else "u") +
                   str(min(4, b["calls"])) + ("e" if b["errors"] + b["fmt"] else "") for b in st["br"])
        return (s.standard, task["family"], q, br, s._reuse_pr(st) is not None)

    OPS_OF = {"F:reuse": "inherit", "F:blind": "compress", "F:vote": "vote", "restart": "heal", "open": "explore",
              "cross": "fuse"}

    def op_of(s, fam):
        """Host families -> common operator names (TRANSPLANT): O-trace plan reuse = INHERIT; blind plan (keys only, the
        runtime computes: a hologram of the task) = COMPRESS; vote where uncertain = VOTE; restart a stuck attempt = HEAL;
        open a new attempt = EXPLORE (P7); cross = FUSE (joint)."""
        return s.OPS_OF.get(fam)

    # ---------- value and report ----------
    def objective(s, st):
        est = st["done_est"]
        if st["ti"] < s.n_tasks and (not st["sim"] or st["ti"] == st["ti0"]):
            est += s._sim_right(st) if st["sim"] else s._p_majority(st)
        return (est / s.n_tasks, -float(st["tok_total"]))      # free-resource row (14:15): result first, then fewer tokens

    def report(s, st):
        return {"result": sum(st["correct"]) / s.n_tasks, "resource": st["tok_total"] / 1000.0,
                "tokens_calls": st["tok_total"], "tokens_forecast": 0, "unit": "accuracy per kilotoken",
                "errors": list(st["errors"]), "failed_calls": st["failed_calls"], "usage_estimated": st["usage_est"],
                "text_toolcalls": st["text_toolcalls"], "withheld_tasks": st["withheld_tasks"],
                "plan_calls": st.get("plan_calls", 0), "plan_failures": st.get("plan_failures", 0),
                "plans_reused": st.get("plans_reused", 0), "blind_answers": st.get("blind_answers", 0),
                "blind_fallbacks": st.get("blind_fallbacks", 0)}
