# A3 report: head to head against compact agent protocols (Slipstream-style, ACCP-style)

Pre-registration: `PREREGISTRATION_A3.md` (commit d4e8df3, before any code; amendment 1 at 8408a00, before the main
run). Harness: `a1_agents.py` (D and E added, commit 8408a00, the code of every live run). Runner: `a3_run.py`.
Analysis: `a3_analyse.py` (commit 2975379). Results: `results/a3_head_to_head.json`, **results_sha256
`ff058345292abb4e7d062c863eeb7f90fc4d493c08fee6cdb108d4a8328ae135`**; per-run records `results/a3_runs.json`
and `results/a3_results.jsonl`; every message and LLM call `results/a3_transcripts.jsonl`.

D and E are **re-implementations from the published descriptions** ("-style"). They are not the original Slipstream
or ACCP systems.

Host: planner → worker → checker, all `claude-haiku-5-5` (headless `claude -p`, no tools). 16 tasks (seeds 100–107
and 300–307) × 4 conditions = 64 task runs, 3,200 real LLM calls, $1.38 recorded. 14 change requests on a 30-line
state, 3 injected drifts per task (48 per condition).

## Strongest finding

**The compact protocols compress, but neither keeps the copies true, and the two fail in opposite ways.**

- **D (Slipstream-style anchors) is the most compact protocol in the test:** 1,468 channel tokens per task, 0.54× of
  P, with **16/16 exact successes**, the same as P. It never sees drift. **40 of 48 injected corruptions were still
  in the worker's replica at the end of their tasks**, and **0/16** tasks ended with all copies correct (P: 16/16).
  The authoritative state stays right only because, in this task, nothing ever reads the worker's copy. The
  corruption is latent: invisible to the protocol and harmless only until a computation depends on that copy.
- **E (ACCP-style deltas) sees drift, because a corrupted working copy shows up in the delta. It can repair it only
  through the LLM**, and that cascades. The checker rejects the unrequested line, the worker often cannot remove it,
  the step fails, and the line returns in every later delta. **59 of E's 60 failed steps carried a drifted line.**
  The result: **1/16** exact successes, 61 wrong final lines, 62.9 calls per task (P 43.1), 286 s (P 192 s).
- **P is the only protocol where compression and integrity hold together:** 48/48 drifts repaired before any model
  call, 0 corruptions left in any copy, 16/16 exact and 16/16 replica-consistent, 0 LLM tokens spent on recovery.

The palace's distinguishing property against the strongest compact protocols is **integrity at near-compact cost**,
not compression.

## Results (means per task, all 16 tasks)

| | P · palace | A · JSON full state | D · anchors, Slipstream-style | E · deltas + seq, ACCP-style |
|---|---|---|---|---|
| Exact success (authoritative state) | **16/16** | 4/16 | **16/16** | 1/16 |
| Replica-consistent success (every copy true) | **16/16** | 4/16 | 0/16 | 1/16 |
| Wrong final lines (sum) | **0** | 15 | **0** | 61 |
| Channel tokens (95% CI) | 2,699 (2,552–2,887) | 17,442 (17,075–17,761) | **1,468** (1,406–1,542) | 2,773 (2,595–2,944) |
| Channel bytes | 10,062 | 46,896 | **4,930** | 9,880 |
| LLM tokens billed | 84,790 | 118,528 | **83,563** | 122,581 |
| billed, scaffold subtracted | 24,129 | 46,548 | **23,425** | 34,408 |
| Output tokens | 6,973 | 15,414 | **6,785** | 8,497 |
| LLM calls | 43.1 | 51.3 | **42.8** | 62.9 |
| Wall-clock (s) | 191.7 | 250.8 | **191.0** | 286.0 |
| Steps failed after 2 retries (sum) | 2 | 17 | **0** | 60 |
| Drift healed by the end of its step | **48/48** | **48/48** | 3/48 | 18/48 |
| Drift healed with 0 model calls | **48/48** | 0/48 | 0/48 | 0/48 |
| Drift in the authoritative final state | 0 | 0 | 0 | 1 |
| Drift in any copy at the end | **0** | 0 | 40 | 6 |
| Recovery per healed drift: channel tok | 37.9 | 901.5 | 0 (incidental) | 96.2 |
| Recovery: LLM tokens billed / seconds | **0 / 0 s** | 7,356 / 16.5 s | 0 / 0 s (incidental) | 4,282 / 9.6 s |

D's one-time concept table (40 key anchors + 17 value anchors) is 202 tokens; with it counted, D is 1,670 tokens per
task. D's 3 heals were incidental. In seeds 102, 106 and 306 the planner listed the full intended state in its
instruction, and the worker re-set the corrupted line along with the requested edit. No rejection or extra call
was involved.

**Split by seed set.** The pattern holds in both halves:

| | P | A | D | E |
|---|---|---|---|---|
| Seeds 100–107 (A1's): exact / replica-consistent | 8/8 · 8/8 | 3/8 · 3/8 | 8/8 · 0/8 | 1/8 · 1/8 |
| Seeds 100–107: channel tok | 2,788 | 17,245 | 1,506 | 2,856 |
| Seeds 300–307 (new): exact / replica-consistent | 8/8 · 8/8 | 1/8 · 1/8 | 8/8 · 0/8 | 0/8 · 0/8 |
| Seeds 300–307: channel tok | 2,611 | 17,639 | 1,430 | 2,691 |

Compared with A1 on the same seeds 100–107: P 8/8 now vs 7/8 in A1, and A 3/8 now vs 5/8. The LLM-error component
varies between runs at this sample size.

## Where P's extra channel tokens go (means per task)

| Edge | P | D | E |
|---|---|---|---|
| planner → worker (instruction) | 1,349 | 1,093 | 1,338 |
| worker → checker (edits) | 196 | 134 | 454 |
| checker → worker (verdicts) | **854** | 111 | 824 |
| checker → planner (forward) | 187 | 130 | 158 |
| heal | 114 | — | — |

Of the 1,231-token gap between P and D, 743 tokens are the checker → worker verdict format that P inherited
unchanged from A1: a JSON verdict with a reason on every approval, where D sends a bare `Accept Edit`. Another 256
tokens are D's anchor quantisation of keys inside the instruction. Neither is part of the palace mechanism. The
palace's own integrity layer (`@state#hash` headers, trailing green dots, White Dragon heals), measured from the
transcripts, is **340 tokens per task**. Projection, not a run: D's formats plus this layer ≈ 1,468 + 340 = 1,808
tokens, i.e. 1.23× D, which would still narrowly miss R1's 1.2×. A palace that used D's verdict and anchor formats
has **not been run**.

## Predictions

| | Prediction | Result | |
|---|---|---|---|
| R1 | channel tokens P ≤ 1.2 × min(D, E) | P 2,699; D 1,468; E 2,773 → **1.84×** of D | **Fail** |
| R2 | P heals 100% with 0 model calls; D and E each fewer | P 48/48; D 0/48; E 0/48 (A 0/48) | Pass |
| R3 | P exact successes ≥ D and ≥ E | P 16, D 16, E 1 | Pass (tie with D) |
| R4 | P tokens per healed drift ≤ 0.25 × D's and E's, (a) channel + billed and (b) channel alone | E: (a) **0.0087×** pass, (b) **0.39×** fail. D: its 3 heals were incidental and cost 0 extra tokens, so no ratio is possible | **Fail** |

## What failed and what it means

- **R1 failed, by a wide margin.** The palace as run in A1 is not the most compact protocol: Slipstream-style
  anchors with bare acknowledgements are 0.54× of P. The gap is in formats P inherited from A1 (verdicts, unquantised
  keys), not in the palace's integrity layer, but that is an accounting result, not a run. A compact palace (the
  green dot and White Dragon on top of anchors and bare verdicts) is the next test, not a claim.
- **R3 passes only as a tie with D, and D's tie is fragile in a specific way.** D's authoritative state was right in
  16/16 tasks because the injected corruption sat in a copy that this task never reads. In 0/16 tasks were all of
  D's copies right. R3's authoritative definition cannot tell these apart; the replica-consistent measure can.
- **R4 failed on channel tokens against E.** E's repair messages are small (a short NAK and a short delta, 96
  tokens) against P's 38. Once the LLM work is counted, P's repair costs 0.9% of E's (38 vs 4,378 tokens, 0 vs
  9.6 s). Against D, R4 cannot be computed: D repaired drift only by accident, at no extra cost.
- **Truncation (secondary, offline, tail cut 10–50% of every recorded worker → checker message, strict decode):**
  P detected 1,165/1,165 and A 1,490/1,490 cuts. **D silently accepted 13/1,150 and E 99/1,955**, cuts that ended on
  a line or item boundary or left a shorter value that is still valid (a cut delta still looks like a valid delta).
  No content hash means no truncation guarantee. Resend cost of one message: D 9.3 tokens, P 13.5, E 18.6, A 349.

## Integrity of this run (reported failures)

- **Amendment 1 (before the main run):** on the smoke seed 999, E's worker could not see that its delta carried the
  corrupted line and re-sent it three times. D and E workers now see, on a retry, the line changes their rejected
  message carried. The amendment favours D and E; P and A were not changed.
- **The batch stopped at 53/64 runs** when the account hit its usage limit. The 53 finished runs had full
  transcripts but no result records, so `a3_run.py` rebuilt them by **exact replay**: the recorded outputs were fed
  back in order, every prompt was checked to be identical, and every replay reproduced the live log line
  (53/53 log lines identical: success, accuracy, channel, billed tokens, calls, drift). For replayed runs, wall-clock is the sum of their recorded LLM-call seconds. The
  11 runs in flight at the stop were run again live from scratch. The LLM calls of the interrupted attempts are not
  in the recorded cost.
- **Analysis correction (before the report, after the first numbers):** A1's recovery measure counts every checker →
  worker message at a drift step as a rejection. That holds for A, but in D and E the same edge also carries
  ACCEPT/ACK, so the first pass charged D's incidental heals 6 tokens each and E an extra ACK. `a3_analyse.py` now
  counts a checker → worker message as a rejection only if no checker → planner forward follows in the same step and
  attempt. The values for P and A are unchanged. Hash before the correction: `9e21c6da…` (and the first pass
  `b5230d57…`); final: `ff058345…`.

## Limits

One model family (Haiku-class, CLI-default temperature), 16 tasks. The success differences against A and E are
large; the tie between P and D is exact. D and E are re-implementations from public descriptions: the full ACCP
draft text could not be fetched here, and Slipstream's own embedding quantiser was not used, since the harness
quantises losslessly, which is in D's favour. The task is structured state editing in which no agent reads another
agent's copy for computation. That is exactly what hides D's latent corruption.

## Next discovery action

**A4: does latent drift turn into wrong results?** Same harness, with one change: the worker computes from its own
copy (the planner sends "increase X by 1", "copy X to Y", "transfer owner A → B" unresolved). Prediction: D's 40
latent corruptions become authoritative errors whenever a computation touches them, so D's exact successes drop
below P's. P stays 16/16. Run it together with **P-compact** (green dot + heal on top of D's anchors and bare
verdicts) to test whether the palace can meet D's 1,468 channel tokens while keeping 48/48 zero-call heals.
