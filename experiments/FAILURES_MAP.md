# Failures map: every pre-registered failure, its objects, and whether the White Dragon's logic applies (D84, D90)

17 Nov 2026. "Objects" names each side of the failure in one word, as the owner asked (17:11–17:16).
"Dragon logic" = the White Dragon (who knows) chooses where to land, at what depth and order, and predicts the
gain; the hologram = the whole held in every part, so a reference replaces resending.

| # | Test | Failure | Objects | Dragon logic applies? | Next landing |
|---|---|---|---|---|---|
| 1 | A3 R1 | Palace 1.84× the tent's size | Palace / Tent | **Yes** | **Tested in A3b: H-dragon 0.64× the tent (BPE 0.55×) with 16/16 replica-consistent → passed B1. 5× (B2) failed: 87% of what remains is lossless planner prose.** Next: A3c |
| 2 | A3 R4 | Repair 38 vs 96 tokens (0.39×) | Palace / Workshop / Tent | **Yes** | **Fixed in A3b (B7): heal 0 tokens per drift (H-dragon), 2.0 (H-copy); 18.5 if both copies are corrupted (offline)** |
| 3 | A1 P2 | JSON checker with memory also caught all drift | Palace / Archive | Partly | Advantage is healing without the model; test where the archive must pay to repair |
| 4 | HT1 K1 | Typed symbols not faster, elements dropped | Hand / Keyboard | **Yes** | Keyboard layer after a learning phase (HT2) |
| 5 | T7 | Meaning not robust to 10% relation noise (47.5%) | Map / Fog | **Yes** | Green dot per relation + heal from the book |
| 6 | T5 | Predicted sign change across hosts absent | Seed / Soil | Partly | Dragon chooses the host binding per host, predicts the sign |
| 7 | R-003 | Move + pierce negative in 40/40 worlds | Arrow / Wall | Yes | Dragon sets the order (pierce before move, or the reverse) and predicts |
| 8 | R-004 | Four placement rules did not hold | Room / Furniture | Yes | Dragon derives placement from depth and order (A2 map) |
| 9 | U1 P3, U1b P2–P3 | Node-universe predictions; 6 nodes without trigger | Star / Orbit | Partly | Dragon assigns missing triggers; retest |
| 10 | S1 P1–P2 | Colour-map predictions | Prism / Light | Partly | Lenses chosen by the dragon instead of fixed regexes |
| 11 | S2 P1 | VAKOG lens rose 1.8×, not 2× | Body / Lens | No (threshold miss) | Keep as measured |
| 12 | E1 P2, P5, P6 | Growth predictions | Tree / Branch | Yes | Knowing landings instead of blind growth (A2 showed blind harms) |
| 13 | V1 P1–P3, P5 | Four thresholds (main effect held) | Key / Lock | Partly | Retest on people (neuroscience row) |
| 14 | H1 all three | Predictive heal missed thresholds, cost bytes | Guard / Gate | Yes | Hologram heal by reference (cheaper) |
| 15 | H2 P1, P3 | Herding in host-reported lack | Flock / Shepherd | Fixed | H2b passed (net of help in flight) |
| 16 | F1 P1–P2 | Feedback halved useful share | River / Dam | Fixed | F1b: scored fairly, roots improved |
| 17 | F1b P1–P3 | Entry reinforcement +0.02, less steady | Seed / Storm | **Yes** | Replace blind reinforcement with knowing landings (A2) |
| 18 | H3c P2 | 50.3% of oracle gain (just passed) | Mirror / Oracle | Yes | Every book carries its test (more measurable versions) |
| 19 | I1 | IMIP does not track its claim (ρ 0.09) | Compass / North | Yes | Dragon redefines the instrument from what it must measure |
| 20 | I2 | CRI and ARC do not track their claims | Scale / Weight | Yes | Same as 19 |

**Pattern:** 14 of 20 are failures of blind choice (fixed rules, random growth, resending, typing); the dragon's
knowing landing and the hologram address them directly. 2 are already fixed (H2b, F1b scoring); 4 are threshold
misses or need people. Each "Yes" is a hypothesis to pre-register, not a result.

## New from A3b (17 Nov 2026)

| # | Test | Failure | Objects | Dragon logic applies? | Next landing |
|---|---|---|---|---|---|
| 21 | A3b B2 | Hologram 1.57× smaller than the tent, not 5× | Hologram / Prose | **Yes** | A3c: shared predictor as reference beam for prose (owner decision on local model) |
| 22 | A3b B6 | Dragon predicted 321 tok/task, measured 932 (−66%) | Dragon / Template | Partly | Dragon saw 2 example steps; give it coverage statistics, it flagged the risk itself |
| 23 | A3b H-copy B3/B4 | 12/16 exact (LLM edit errors, approved by checker) | Copy / Error | No (LLM variance) | Keep as measured; codec cannot make an approved edit right |

### Answered since A3b

- **21 (A3b B2, 5× not reached): answered by A3c.** H-pred 0.141× D in BPE with 0 model calls; H-local 0.106× D in
  BPE with full integrity (C3 pass). The prose floor fell to 0.60 / 0.41 bits per character.
- **22 (dragon size prediction −66%): answered by A3c.** With coverage statistics, the dragon predicted H-pred within
  +5.4% (C4 pass) and H-local within −3.7%.

## New from A3c and A4 (17 Nov 2026)

| # | Test | Failure | Objects | Dragon logic applies? | Next landing |
|---|---|---|---|---|---|
| 24 | A3c C1 | H-pred size and integrity pass (0.141× BPE, 48/48, 0/1,160), but 15/16 replica-consistent: checker rejected a correct `DEL` 3× (seed 300) | Checker / Error | No (LLM variance; codec byte-exact) | Error-source split: rerun H-pred on the same steps to measure the checker's model-error rate |
| 25 | A3c C2 | H-pred 15/16 exact vs D 16/16 (same seed 300 step) | Checker / Error | No | Same as 24 |
| 26 | A4 L2 | H-dragon 15/16 exact and replica-consistent: worker wrote a wrong value from a true, healed copy (seed 407, step 6); 0 drift-traced errors | Worker / Error | No (LLM variance) | A4 next action 2: 3× reruns of the 128 compute steps to separate protocol from model noise |

**Pattern across 23–26:** every remaining failure of the integrity protocols is a single model error on a true copy,
approved or rejected wrongly by an LLM, never a codec or integrity failure. The registered rule counts them, as it
should. The open question they share is the base rate of model error per step, which none of the tests has
measured yet; one error-source experiment answers 23–26 together.

## New from A5 (18 Nov 2026)

| # | Test | Failure | Objects | Dragon logic applies? | Next landing |
|---|---|---|---|---|---|
| 27 | A5 K1 | X3 0.581× / 0.828× of the honest market best (target ≤ 0.1); X5 (secondary) 0.268× / 0.354× | Cost / Thinking | **Yes** | A5b: thinking control applied equally to B1 and X5 (counterfactual ≈ 0.12, unmeasured) |
| 28 | A5 K2 | X1s calls 0.51× / 0.63× (target ≤ 0.4): the audit rule selects 10–12 of 14 steps | Audit / Calls | Yes | Audit by equality (second planner translation, model audit only on disagreement) |
| 29 | A5 K3 | X2 output 0.36× / 0.54× (target ≤ 0.25): X planners think more than B1's | Planner / Thinking | Yes | Worked examples and templates; thinking control |
| 30 | A5 K4 (X3) | X3 replica 15/16 on both sets: auditor false rejects (palace notation read wrongly) | Palace notation / Auditor | Partly | Drop palace notation in prompts at this scale; audit by equality |
| 31 | A5 X1s S2 seed 403 | The only audit miss in 192 tasks: a compute written as a literal `SET`, unsampled | Risk class | Yes | Risk class from the request's verbs as well as the operations |

**Pattern:** the integrity layer held everywhere (48/48 heals, 0 drift-traced values, 0 wrong steps approved by the
audit). The cost gap is now thinking tokens and audit calls, not calls per step; the assembly line removed the
per-step dependency.

## New from A7a (18 Nov 2026)

| # | Test | Failure | Objects | Dragon logic applies? | Next landing |
|---|---|---|---|---|---|
| 32 | A7a P1 | M\* (B2) 15/16 and 16/16 exact, never ≤ 13/16; its one failure is a REHOST step (S1 seed 107) uncorrected by 2 retries | Runtime / Patch | Partly | A7b depth 16 / horizon 224 (P9), where state-dependent steps dominate |
| 33 | A7a P3 | X5b cost per correct 0.787× / 0.910× of B2 (target ≤ 0.5); REACH distance 1.27× / 1.10× | Cost / Scale | Yes | Grow state, not requests (P10); thinking off (P3b) |
| 34 | A7a P4 | Blind input 1.07× / 1.14× B2, not ≤ 0.5×: the grammar outweighs a 30-key state | Grammar / State | Yes | Compress the operation grammar to a static cached prefix; test at larger state |
| 35 | A7a P5 | B2 thinking 1.10× / 1.05× X5b, not ≥ 2× | Planner / Thinking | No (at this scale) | A7b thinking-off cell |

**Pattern:** at A5's scale M\* is a near-tie. RSOS's measured edge is one error class (values computed from state),
seen once. The tests that can show a large gap are the scale cells in A7b.
| 36 | A7b think-off | Thinking control failed: `MAX_THINKING_TOKENS=0`, `alwaysThinkingEnabled:false` and `--effort low` all ignored by the CLI for Haiku 5.5 (S1: 0/48 tasks at 0 thinking); P1b, P3b no verdict | Switch / Model | No (instrument failure) | Amendment: a thinking control the API honours (direct API call with thinking disabled, or a model without adaptive thinking), replay-checked before rerun |
| 37 | A7b P9 | On L2 (224 steps) B2 15/16, not ≤ 8/16; long chains do not break one-plan M\*. All 7 B2 failed steps in 96 long tasks are REHOST (4) or INHERIT (3), X5b 0 | Chain / Scan | **Yes** | A cell that targets set-scan requests (REHOST/INHERIT density, owners over 300 keys), not chain length |
| 38 | A7b P10 | X5b input L3 ÷ L1 = 1.528 (≤ 1.5 missed by 0.028); B2 2.154 (not ≥ 3): request text dominates both prompts | Names / Values | Yes | Name services by reference (a hologram index) so input does not grow with key names |

## A8 (18 Nov 2026)

No A8 prediction failed on the Claude ladder (G1–G5 pass). Instrument note, not a prediction failure:
| 39 | A8 Groq smoke | HTTP 403 / Cloudflare 1010 on the free-tier backend (default Python user agent); 0 tasks ran | Agent / Edge | No (transport) | Fixed by amendment (`User-Agent` header); rerun the free-tier cells |

## A8, other families (19 Nov 2026)

| # | Test | Failure | Objects | Dragon logic applies? | Next landing |
|---|---|---|---|---|---|
| 40 | A8 G7 part 2 | Invalid operations proposed per blind task: non-Claude 0.16 vs Claude 0.09 (1.7×, not ≥ 3×); Gemini proposed none. All rejected before execution (part 1 holds) | Grammar / Family | Partly | Measure per family as more run (Codex, Qwen, small models); grammar examples only if a family needs them |
| 41 | A8 G8 (**closed 19 Nov: met** — 712#35 failed on Gemini and GPT-6.2 Sol) | No single failing step shared by two non-Claude families yet: 712#35 fails on Gemini and Claude, 702#35 on Mistral and Claude | Request / Family | Yes | More families on L3 (OpenAI via Codex) |
| 42 | A8 gpt-oss cell | Groq free tier: X5b S1 3 of 16 tasks (daily quota); L3 not runnable (8,000 tokens a minute). `a8_analyse.py` reports G1 and G5 false from this incomplete cell | Quota / Analysis | No (instrument) | Finish on Groq or via Codex; the analysis should mark incomplete cells (amend before the next scoring) |

## SC1, robot scene (19 Nov 2026)

| # | Test | Failure | Objects | Dragon logic applies? | Next landing |
|---|---|---|---|---|---|
| 43 | SC1 P4 on Gemini | Gemini's JSON Patch failed 906 step 45 (5 objects), not one of the five named hand-overs; P4 passed only on Mistral (913/53, 913/49). Selection by object count was too coarse: 906/45 is the only SC1 hand-over where every matched object arrived during the task | Scan / Start state | **Yes** | SC2: a frozen predictor of out-of-date matches, tasks from a public beacon |
| 44 | SC1 X5b invalid operations | Mistral's RSOS planner proposed 3.3 invalid operations per task (53 in 16; Gemini 0); all rejected before running, all tasks exact | Grammar / Vocabulary | Partly | grammar examples in the scene vocabulary (later amendment, not in SC2) |

## SC2 (19 Nov 2026)

| # | Test | Failure | Objects | Dragon logic applies? | Next landing |
|---|---|---|---|---|---|
| 45 | SC2 Q4 | Channel on FLOW steps 0.104× the bytes of JSON Patch + digest, not ≤ 0.1× (measured at export, before any run); the 12-digit digest is 13 of the ~45 bytes of a FLOW message | Channel / Digest | Partly | report the program alone beside the program + digest |
| 46 | SC2 Q6 | Frozen predictor expected 7.6 JSON Patch failed steps on Mistral (interval 2–14), observed 22: it had never seen an operation that computes per match | Predictor / Compounding | Yes | add the per-match computation factor; refit only after SC2, freeze again before the next draw |
| 47 | SC2 Q10 | Control: JSON Patch failed 11.7% of the same requests with every object named vs 14.8% when it had to find them (1.27×, not ≥ 2×). Finding is not the main cause; producing many values from changed state is | Law / Cause | **Yes** | restate the law's second factor; test "values to produce" directly |
| 48 | SC2 Q11 | **First RSOS blind task failures:** SC2-C on Mistral 14/16; on two tasks the planner's operations for long object lists (up to 19 objects, one line each) were rejected three times, the step was not executed, later steps read unmoved values. None silent | Planner / Long lists | **Yes** | FLOW for such requests (16/16); a list form of INHERIT; retry with the runtime's error per object |
| 49 | SC2 Gemini | Prepaid credit exhausted mid-run (HTTP 402): Gemini SC2 and SC2-C incomplete, not scored | Quota / Run | No (run) | resume after top-up |
| 50 | SC2 harness | The FLOW extension's error message named the wrong field ("unknown field in 'y'" for `OVER name`), so RSOS retries on the control could not correct | Harness / Feedback | No (our bug) | fix in a new module before SC2-C2; frozen SC2 files unchanged |
| 51 | SC2 output cap | 16,000 max_tokens per call: Mistral's thinking used up to 15,999; both RSOS control failures and 9 of 10 JSON Patch control failures hit the cap; confounds Q10 | Settings / Budget | Partly | SC2-C2 without a cap below the model's maximum, pre-registered |
