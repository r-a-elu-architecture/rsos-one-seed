# Phase 3 results (confirmatory; sealed 1a9c909; analyze_phase3.py exactly as PREREG_AGENTS_PHASE3.md)

Run on the owner's laptop, 22 Nov 2026 ~13:45–18:00 Kyiv, OpenRouter. 1,200 paired units per arm (4 models × 300 tasks:
staff 5000–5149, orders 3000–3149), 0 infrastructure errors. Data: phase3_staff.jsonl, phase3_orders.jsonl (commit
4228aac). Analysis reproduced here byte-for-byte on the pushed data (same RESULTS_PHASE3.json numbers).

## Sealed hypotheses
| ID | Test | Result | Verdict |
|---|---|---|---|
| **H1 (primary)** | rsos_01100 > react, pooled | 91 wins / 75 losses, p = 0.12 | **FAIL** |
| H2 | > react within each model (Holm), only if H1 passes | Llama 46/37, gpt-oss-120b 9/4, gpt-oss-20b 36/34, Qwen 0/0 | **FAIL** (not reached; none significant) |
| H3 | > reflexion / selfcons / planexec, Holm | 81/78, 93/96, 103/90 | **FAIL** |
| **H4** | tokens per correct answer vs selfcons < 0.80 AND accuracy not more than 3 points worse | ratio **0.597** (95 % CI 0.575–0.620); accuracy −0.25 pts (CI −2.5 to +1.9) | **PASS** |

Accuracy (pooled): selfcons 0.887, **rsos_01100 0.884**, reflexion 0.882, planexec 0.873, react 0.871.
Mean tokens per task: react 4,149; planexec 5,175; rsos_01100 5,548; reflexion 5,562; selfcons 9,316.

## What it means
- **The structure did not beat the standard agent loop on new tasks and other models.** H1 fails. The phase 1d
  margin (+8 points over react on gpt-oss-20b) did not replicate: on gpt-oss-20b here, 0.787 vs 0.780, while
  selfcons (0.873) and planexec (0.880) were higher. Phase 1d's gain was mostly the winner's curse of choosing the best
  of four structures on the same 100 tasks, as the pre-registration warned.
- **H4 passes, and it is a sealed layer-1 (blue) result:** the structure is as accurate as self-consistency at
  **0.60× its tokens**. Honest scale: self-consistency runs the task three times, so one run plus a check being
  cheaper is expected; the result is that the accuracy holds at that price.
- **Two of four models were at the ceiling** (Qwen 3.8: 1.00 for rsos and react, 0 discordant tasks; gpt-oss-120b
  0.95–0.97), so they could not show a difference either way. Descriptive only: on the model with the most room
  (Llama 4 Scout) rsos_01100 was highest (0.783 vs react 0.753, selfcons 0.727, planexec 0.667); this is not a
  confirmed claim.
- Roadmap: **no colour change**; no cyan for the agents row. H4 is recorded as blue evidence (cost at equal accuracy).

## Descriptive (not sealed): cost per 1,000 tasks, errors × cost per error + tokens at $0.05 per million
| Cost per error | react | rsos_01100 | reflexion | planexec | selfcons |
|---|---|---|---|---|---|
| $0.01 | $1.50 | **$1.44** | $1.46 | $1.53 | $1.60 |
| $1 | $129 | $116 | $119 | $127 | **$114** |
| $100 | $12,917 | $11,584 | $11,834 | $12,667 | **$11,334** |
| $1,000 | $129,167 | $115,834 | $118,334 | $126,667 | **$113,334** |
Where errors are expensive, the most accurate arm wins (selfcons by 0.25 points, within noise); where compute dominates,
rsos_01100 is cheapest of the accurate arms.

## Signal for the next build (fever principle)
The single structure (detect + adapt) helps only where the model has room and adds little where the model already
verifies itself. Same diagnosis as DIAG1 in the twins: the structure adds too little over its own base loop. The
next agent structure should come from Part I (problem B: joint choice, value carried back, reinforce what worked),
selected on a model with headroom, with the ceiling models replaced or given harder tasks.
