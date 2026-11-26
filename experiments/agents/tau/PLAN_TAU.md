# τ-bench test of the RSOS structure: preparation (22 Nov 2026, not yet sealed)

Why τ-bench: the industry's reference test for tool-using customer-service agents (Sierra / Princeton; leaderboard at
taubench.com). An agent talks to a simulated customer, follows a written policy, and calls the shop's or airline's
real API tools; it scores only if the final database state and required outputs are exactly right. The structure's
roles (no repeated failure, check before a change, re-plan, lessons, regulation) match the field's known failure mode
there: wrong or unauthorised write actions.

## What is ready
- `rsos_tau.py`: the structure as a τ-bench agent on top of the official `llm_agent` (same prompt, same tools, same
  generate()), plus registration of τ-bench's own ReAct example as a second baseline. Written against
  sierra-research/tau2-bench commit 768f3d8 (20 Nov 2026), which the run pins. Not yet run (no network here): a
  2-task smoke run on the laptop comes first.
- Domains in that commit: airline (50 base tasks; test split 20), retail (114; test 40), telecom (2,285).

## To be sealed after phase 1d / phase 3 (nothing below is fixed yet)
- The structure code = the one phase 1d selects (and phase 3 confirms).
- Arms: llm_agent (official baseline), react_example, rsos_<code>. Same agent model, same user model, same seeds.
- Split: retail + airline **base** (164 tasks), 3 trials each (pass^1 and pass^3, the board's measures).
- Agent model: openrouter/openai/gpt-oss-20b (and later the other phase 3 models). User simulator:
  openrouter/openai/gpt-oss-120b for all arms (the board uses gpt-4.1; our absolute scores are therefore not board
  scores; the comparison between arms is exact because every arm meets the same simulator and seeds).
- Analysis: per task, paired; rsos vs each baseline, one-sided sign test on the tasks where they differ, Holm.
- **Public prediction before the run** (step 4 of the plan): where the structure helps (tasks with write actions that
  the policy restricts) and where it does not (read-only or single-action tasks), with the expected sizes, committed
  and timestamped before any call.

## Cost and time (estimate, to be measured in the smoke run)
Each conversation is ~10–30 agent turns with the long policy in context; roughly 100–300k tokens per task-trial for
agent + user. 164 tasks × 3 trials × 3 arms ≈ 1,500 conversations ≈ 150–450M tokens: about **$15–45** on gpt-oss
prices, 4–10 hours. One trial first (~$5–15) is the sensible start.

## Laptop setup (later, when sealed)
```powershell
cd D:\FROM_CLAUDE
git clone https://github.com/sierra-research/tau2-bench.git
cd tau2-bench
git checkout 768f3d8
python -m pip install uv
uv sync
# key: the same $env:OPENROUTER_API_KEY (LiteLLM reads it)
uv run python D:\FROM_CLAUDE\RSOS-Multimodal-World\experiments\agents\tau\rsos_tau.py run --domain retail --agent rsos_11011 --agent-llm openrouter/openai/gpt-oss-20b --user-llm openrouter/openai/gpt-oss-120b --num-trials 1 --num-tasks 2
```
