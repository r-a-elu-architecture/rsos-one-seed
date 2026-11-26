# RSOS-StateBench v1: multi-agent shared state

80 tasks where agents edit one shared configuration state, from the pre-registered experiments A5 and A7: S1 and
S2 (30 keys, 14 requests), L1 (56 requests with dependency chains), L2 (224 requests, chains of 29–73 dependent
changes) and L3 (56 requests on a 300-key state). Each task gives the start state, the requests in order, the true state after
every step, the final truth and the drift events of the integrity test. **Use any framework, any model, any number of
agents**, write your final states to a JSONL file and score it. No RSOS code is needed.

| File | Content |
|---|---|
| `statebench_v1_S1.jsonl` | 16 tasks (seeds 100–107, 300–307), sha256 `0c76c17d7d57859e…` |
| `statebench_v1_S2.jsonl` | 16 tasks (seeds 400–415), requests that depend on earlier values marked `Worker-computed:`, sha256 `11c5b8d4a8b460db…` |
| `statebench_v1_L1.jsonl`, `_L2`, `_L3` | 16 tasks each (seeds 500–515, 600–615, 700–715) |
| `statebench_v1_SC1.jsonl` | 16 tasks (seeds 900–915): a robot scene shared by six robots, 50 objects × 6 fields = 300 keys, 56 requests; mapping in `experiments/PREREGISTRATION_SC1.md`; sha256 `db6b59e77c0e4ca7…` |
| `score.py` | the scorer (0 model calls); scores every set present in the submission |

```bash
python bench/score.py my_results.jsonl --name "my framework + my model"
```

Submission, one line per task: `{"set": "S1", "seed": 100, "final_state": {...}, "calls": 2, "cost_usd": 0.0012}`
(`calls` and `cost_usd` optional; cost per correct task is computed when every task has a cost). The `drift` events
are optional: inject them into one agent's copy before the given step if your system keeps several copies.

## Leaderboard, long tasks (L1 + L2 + L3, 48 tasks)

| System | Model | Exact | Failed steps | Cost per correct task (L1 / L2 / L3) | Planner sees values | Source |
|---|---|---|---|---|---|---|
| RSOS blind (X5b) | Haiku 5.5 | **48/48** | **0** | **$0.0037 / $0.0138 / $0.0044** | **no** | A7b |
| One-call JSON Patch + audit (M\*), same hash check | Haiku 5.5 | 46/48 | 7 (all state-dependent) | $0.0054 / $0.0208 / $0.0087 | all | A7b |

## Leaderboard, across Claude models (S1 + L3, 32 tasks each)

| System | Haiku 5.5 | Sonnet 5.5 | Opus 5.5 | Source |
|---|---|---|---|---|
| RSOS blind (X5b) | **32/32** | **32/32** | **32/32** | A7, A8 |
| One-call JSON Patch (M\*) | 30/32 | 31/32 | 32/32 | A7, A8 |
| JSON Patch told to track state (B2s) | 29/32 | — | — | A8 |

## Leaderboard, S1 + S2 (32 tasks)

Exact tasks of 32 (S1 + S2). Cost per correct task at Claude Haiku 5.5 API prices (A5's api basis). Add yours with a
replication issue: the results file, the scorer output and its `submission_sha256`.

| System | Model | Exact | Calls / task | Cost per correct task | Planner sees values | Source |
|---|---|---|---|---|---|---|
| RSOS blind (X5b): operations, runtime computes, one audit | Haiku 5.5 | **32/32** | 2.3 | **$0.00120 / $0.00130** | **no** | A7a |
| RSOS (X5r) | Haiku 5.5 | 32/32 | 2.3 | $0.00125 / $0.00133 | lines named | A7a |
| One-call JSON Patch + audit (M\*), same hash check | Haiku 5.5 | 31/32 | 2.1 | $0.00153 / $0.00143 | all | A7a |
| One model call per step (H-dragon, per-step protocol) | Haiku 5.5 | 31/32 | 42.6 | $0.00460 / $0.00407 | all | A5 |

Costs are S1 / S2. All rows used the same seeds; the A7a rows also the same hash check, zero-call healing and audit
rule. Limits: one task family, one model family. Results on other models and frameworks, confirming or not, are the
point of this table.
