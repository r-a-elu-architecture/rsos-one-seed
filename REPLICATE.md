# Replicate the core claims

Three levels: **verify** our numbers in one minute with no model call; **score your own framework** on the same 32
tasks with [StateBench](bench/); or **re-run** A7a or A5 (about an hour; $0 on a Claude plan, under $1 at API prices).

## Verify in one minute (0 model calls)

```bash
pip install -e . tiktoken
python experiments/a7_run.py replaycheck S1      # the A7 harness: every arm, given correct plans, is exact; pass: true
python experiments/a7_analyse.py default         # recomputes results/a7_default.json: results_sha256 42be52d5…
```

## A7a: against the market's most efficient pattern (M*)

**Claim (pre-registered):** with the same model (Haiku 5.5), seeds, hash check, healing and audit rule, one-call JSON
Patch (M\*) was exact on 31/32 tasks; RSOS blind (the planner shown no state value) on 32/32, at 0.787× (S1) and
0.910× (S2) M\*'s cost per correct task. Failure would be: RSOS blind below M\* on exactness, or its cost per correct
task above M\*'s on either set.

```bash
python experiments/a7_run.py run S1              # B2 (M*), X5r, X5b: 48 tasks
python experiments/a7_run.py run S2
python experiments/a7_analyse.py default
```

## A7c: on any laptop, $0, any open model (Ollama)

```bash
ollama pull qwen2.5:1.5b                          # or any model Ollama serves
A7_BACKEND=ollama A7_LABEL=local_qwen15 python experiments/a7_run.py run S1 B2,X5b
# Windows PowerShell: $env:A7_BACKEND="ollama"; $env:A7_LABEL="local_qwen15"; py experiments/a7_run.py run S1 B2,X5b
# other model: set A7_LOCAL_MODEL (e.g. llama3.2:3b) and a new A7_LABEL; a new model is a new result, please label it
```

# A5: one plan against one call per step (about 1 hour, under $1 at API prices)

**Claim (A5, pre-registered):** in a three-agent workflow that edits a shared 30-line state over 14 change requests
with 3 injected drifts, the RSOS assembly line (X5: the model writes RSOS operations for the whole task in one call,
the runtime executes them, one audit call) uses **2.2–2.4 model calls per task instead of 42–43**, costs
**0.268× (S1) and 0.354× (S2)** of B1 (the same agents with one model call per step: RSOS's own per-step protocol, H-dragon) at API prices, and is
**16/16 exact on both sets**. Failure would be: X5/B1 cost ratio above 0.5 on either set, or X5 exact below 15/16.

## What you need

- Python 3.11+, `pip install -e .` and `pip install tiktoken`
- The Claude Code CLI (`claude`), logged in or with `ANTHROPIC_API_KEY` set. Model: `claude-haiku-5-5`
  (any other: `export A5_MODEL=<model id>`; a different model is a new result, please label it).

## Run

```bash
python experiments/a5_run.py replaycheck S1      # offline: the harness reproduces the recorded baseline, 0 calls
python experiments/a5_run.py run S1 B1,X5        # 16 tasks x 2 arms, about 16 minutes
python experiments/a5_run.py run S2 B1,X5
python experiments/a5_analyse.py                 # writes results/a5_cost.json: ratios, CIs, verdicts
```

Run in a fresh clone (the runner appends to `results/a5_results_S*.jsonl`). Compare your `X5 / B1` ratio and exact
counts with the table in `experiments/A5_REPORT.md` §1.

## Check our numbers without any model call

```bash
python experiments/a5_analyse.py                 # recomputes results/a5_cost.json from the recorded runs (sha 9cd1eb92…)
python experiments/a5_runtime_equivalence.py     # the shipped rsoslang.state runtime replays every recorded X5 plan: 32/32 final states match
python experiments/a3c_edges_check.py            # A3c per-edge numbers from text-free counts
```

## Tell us

Open an issue titled "Replication: <model> <date>" with your `results/a5_cost.json`. Every replication, confirming or
not, is listed in the README and credited in the next whitepaper version.
