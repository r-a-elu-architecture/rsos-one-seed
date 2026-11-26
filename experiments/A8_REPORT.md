# A8 report: the Claude ladder and a stronger M\* (Haiku, Sonnet, Opus 5.5; S1 and L3). 18 Nov 2026

Pre-registration: `experiments/PREREGISTRATION_A8.md`; no prediction changed. Replay checks S1 and L3 (with B2s) pass,
0 calls. Smokes S1 seed 999: Sonnet and Opus, B2 and X5b exact. Served model checked with one direct `claude -p` call
per model (`modelUsage` = `claude-sonnet-5-5`, `claude-opus-5-5`); the result files record the requested id. Runs on
the session's OAuth login (owner-approved). One 5-hour usage limit was hit during Opus S1 (31/32 done) and the run
resumed after reset. No task was dropped. Haiku B2 and X5b rows are A7's runs (label `default`), reused as
pre-registered. Analysis ran at commit `873d4a2`.

## Strongest finding

**M\*'s failures sit on the same request in the same task, whatever the model and whatever the instruction.**
- **L3 seed 712, request #35:** "Everything owned by emeka is now owned by dara." It fails for Haiku B2, for Haiku B2s
  (told to track state) and for **Sonnet B2**, each time with the same wrong keys (`dune.owner`, `gateway.owner`,
  `glacier.owner`, `harbor.owner`, `indigo.owner`, …).
- **S1 seed 107, request #14:** "Everything owned by bruno is now owned by chen." It fails for Haiku B2 in A7a and in the A7b
  replicate, and for Haiku B2s.

All **8 of 8** M\* failed steps in A8 are **REHOST** (find every key holding a value, then rewrite all of them). The blind
arm X5b ran **96 tasks on three models and failed 0 steps**. The error belongs to the request class, not to model
noise. A stronger instruction does not remove it: B2s did slightly worse (29/32 against B2's 30/32 on Haiku). A
larger model removes it only at the top: Opus B2 was 32/32. The runtime arm is exact at every size.

## Exact per model and cell (16 tasks each)

| Model | Cell | B2 (M\*) | B2s (M\* + track state) | X5b (blind) | M\* failed steps (kind) |
|---|---|---|---|---|---|
| Haiku 5.5 | S1 | 15 | 15 | 16 | B2 1, B2s 1 (REHOST) |
| Haiku 5.5 | L3 | 15 | 14 | 16 | B2 2, B2s 3 (REHOST) |
| Sonnet 5.5 | S1 | 16 | — | 16 | 0 |
| Sonnet 5.5 | L3 | 15 | — | 16 | 1 (REHOST, seed 712) |
| Opus 5.5 | S1 | 16 | — | 16 | 0 |
| Opus 5.5 | L3 | 16 | — | 16 | 0 |

Drift healed at 0 calls: 48/48 in every new cell.

## Cost per correct task (api basis, $; Opus not priced on the sheet)

| Model | Cell | B2 | B2s | X5b | X5b ÷ M\* |
|---|---|---|---|---|---|
| Haiku | S1 | 0.00153 | 0.00155 | 0.00120 | 0.79 |
| Haiku | L3 | 0.00871 | 0.00918 | 0.00436 | **0.50** (B2s ÷ X5b = 2.11) |
| Sonnet | S1 | 0.01494 | — | 0.01255 | 0.84 |
| Sonnet | L3 | 0.09377 | — | 0.05056 | **0.54** |
| Opus | L3 | tokens: in 15445, think 1831 | — | in 12101, think 719 | input 0.78×, thinking 0.39× |

## Verdicts

| # | Verdict | Measured |
|---|---|---|
| G1 invariance | **PASS** | X5b 16/16 in all 6 cells (Haiku, Sonnet, Opus × S1, L3) |
| G2 error class | **PASS** | 8/8 M\* failed steps state-dependent (all REHOST); X5b 0 failed (0% of M\*'s) |
| G3 cost at 300 keys | **PASS** | X5b ≤ B2 on L3: Haiku 0.50×, Sonnet 0.54× |
| G4 stronger M\* | **PASS** | Haiku B2s 15 ≤ 16 (S1), 14 ≤ 16 (L3); B2s cost per correct 2.11× X5b on L3 (≥ 1.2) |
| G5 no model where M\* wins | **PASS** | B2 never beats X5b; best case Opus ties at 16/16 |
| P11 (A7c) | not run here | local model, owner's PC |

**REACH families:** the analysis lists 3 Claude models with blind 16/16 (`default` = Haiku, `sonnet55`, `opus55`).
That is **1 model family** of the target 10. The family limit is not yet addressed. That needs the free-tier runs (Groq, Google, Mistral,
OpenRouter) and the local models.

## Limits

- One family (Claude) so far. G1/G5 for other families are pending the free-tier runs. The first, Groq, was blocked
  by HTTP 403 / Cloudflare 1010 (default Python user agent). This is fixed by amendment (`User-Agent: rsos-a8/1.0`), replay checks
  re-pass, and no free-tier task ran before the fix.
- M\* failures are few (8 steps in 6 tasks) and concentrated on 2 seeds. That is the finding, but it is also a small base.
  A REHOST-dense cell would turn it into a rate.
- Default thinking only (the off control is unavailable, see A7). Opus is reported in tokens only.

## Hashes

| File | sha256 |
|---|---|
| `results/a8.json` (`results_sha256` field) | `bbf7f31a635f7e882b69caf71fbf235d5ad66246d24e6292ba662b28d75b2fdd` |
| `results/a8.json` (file) | `e0183ea65340d0c5f51c0fe7ca954ed630923e10c618c93921be8f0b95c2dd03` |
| `a7_results_S1_sonnet55.jsonl` | `e92aa13589576e59d5f850ab50d9584ab65a45cc48190c536804ebce75065bbe` |
| `a7_results_L3_sonnet55.jsonl` | `adda261da353160f182aa929be6869ec46e4ed674a2f08dc062a531daf55d9f9` |
| `a7_results_S1_opus55.jsonl` | `50ecc52b96a906c332db07ee6ca497ae213a88a665d95c9e2b556182f7921b77` |
| `a7_results_L3_opus55.jsonl` | `66c7d2d3c4b3037731110a9751ccce878a98ac0e051f772e1b4422e5c764b9c2` |
| `a7_results_S1_haiku_b2s.jsonl` | `3b89c4df2b4625e19d4884942944c50a9f3975715365cc1aee875a59732d770a` |
| `a7_results_L3_haiku_b2s.jsonl` | `e7e1007fc9c45bdddf9152b0ce60214b151bbb94c8bc2ad8b4eb3e7f3a837588` |
| `a7_transcripts_S1_sonnet55.jsonl` | `e0e66d38d6fa8f9876ad24a67ca41082356acadc3a0ad1a4c0206e48879c29a8` |
| `a7_transcripts_L3_sonnet55.jsonl` | `da92d5995fbbda86272a66f6cdd06ed8792d90ecbb716033796cc1a62e1292c2` |
| `a7_transcripts_S1_opus55.jsonl` | `49fe864d44a0eff43f70c0c7abc09d7f32a99191d06770bea5fc1bb995425d8c` |
| `a7_transcripts_L3_opus55.jsonl` | `24a15519ffff15d2b708db4aad044f35c034f3469d63ba8229abcaa36aa8ef95` |
| `a7_transcripts_S1_haiku_b2s.jsonl` | `5c745db8d2f7ba7a870646482e2fe6130d79dafe20b0cbb90cb8ed531f46395e` |
| `a7_transcripts_L3_haiku_b2s.jsonl` | `a1bb50f796fb881131a9820fb0ea8d240b4f54f3dd060561d7ade96b8ad86944` |
