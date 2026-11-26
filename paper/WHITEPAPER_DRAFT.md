# One Selector, Many Domains: a shared decision selector over domain-written candidate sets, sealed against each domain's standard method

**Draft, 26 November 2026, revision 5 (after CONF4–CONF6: the comparison against RSOS-free planning).** Not published. Every result below comes from a
sealed run, and every number links to its result file in this repository. Results that were not shown are reported
alongside those that were. The review's findings and how each was handled are in Appendix A.

**Status:** REAL3 biology is UNDECIDED on 6 of 8 stage-1 cells (the re-run of the timed-out pair was cancelled for
budget; no stage 2). Energy and robotics are reported at their REAL3 levels.

## Abstract
We test one decision selector, the *seed*, across real domains: AI agents, AI-to-AI messaging, AI-to-human replies,
inventory, satellite downlink, energy, robotics, quantum measurement, neural sensing and classification. The selector is
shared and unchanged; each domain supplies candidate actions, including domain-written levers that the hosts map to RSOS
operators. Every test was pre-registered, fingerprinted and pushed before it ran, on fresh paired cells.

- **REAL3** (main run): the seed beats the standard method in **seven of ten** domains under its pre-registered rule
  (four after a Holm correction across units); not shown in quantum and neural sensing; biology undecided.
- **STRUCT1** (ablation): with the domain-written levers switched off, the general structure alone does no better than
  plain rollout in any of five rows (**NOT SHOWN**). The gains come from the levers.
- **Headline, against RSOS-free planning** (plain rollout; levels fixed before each run, fresh cells):
  - **CONF6 met every pre-registered criterion:** with the whole AI–AI system bound to one RSOS structure, two real
    models answered **all 200** fresh questions correctly (plain rollout 0.875) with **51 % fewer tokens**
    (Holm p 1.3e-7 and 5.1e-28).
  - **CONF5 (criteria met in 2 of 3 rows):** in AI agents the full RSOS structure used **43 % fewer tokens at higher accuracy**
    (0.95 vs 0.83, p 1.9e-13); in satellite downlink it won **20 of 20** cells (+0.74 %, p 1.5e-8). Its AI–AI row did not
    pass on tokens; CONF6 re-tested that host with the whole system bound.
  - Three unrelated hosts therefore beat plain rollout at p < 1e-5, each in its own sealed test. STRUCT1 had found that
    the bare structure only matches plain rollout; what beats it is the structure with its operators bound.
- **Three confirmations against the standard on fresh cells** (CONF1–CONF3, levels fixed before each run):
  - **CONF1** met every pre-registered criterion: the full seed beats the standard in AI
    agents, AI–human, inventory and satellite at Holm-adjusted p < 1e-5 (1e-27 to 1e-9). Every lever it used traces
    to an RSOS operator.
  - **CONF3**, an independent higher-powered run designed after CONF1/CONF2's interim results:
    - **communication principle, all criteria met**: 25–61 % fewer tokens at equal or better results in AI agents,
      AI–human and AI–AI, all at p < 1e-7;
    - **cross-domain claim, criteria met in 4 of 5 rows**: 4 of 5 rows, with inventory just above the threshold;
    - **"the language composes winning moves", criteria met**: operator chains written by a fresh agent from the RSOS
      sources beat the standard in 3 of 4 rows. The composed moves carried that gain in satellite and AI–AI; in AI
      agents it came mostly from the shared structure.
- **Two tests that did not reach their levels, reported as they came:** CONF4 (programs written by an AI given the RSOS
  sources vs the same AI without them, both given the same compiled operators: NOT SHOWN, 1 of 4 rows; the passing row is
  AI agents, 44 % fewer tokens, p 4.9e-16) and ABL1 (single operators switched off: NOT SHOWN; the operators chosen were
  barely used, a design error disclosed in §5.7).

Each pre-registration fixes its pass criteria before the run. This paper reports whether they were met (all, partly, or not), with the numbers; it does not rank results. The sealed analysis files name the outcomes UNPRECEDENTED, STRONG and NOT SHOWN; those are internal labels for all, partly and not met, nothing more. They measure statistical certainty and operator lineage, not novelty
against prior art. The individual mechanisms have relatives in recent work (§7); what we found no precedent for is one
operator language bound unchanged across hosts this unrelated, sealed-tested against each host's standard and against
plain rollout. The claim is a sealed, replicated selection discipline over domain-written and language-composed
candidates, not one algorithm that is best in any field.

## 1. The claim, and what it is not
- **Claimed:** one shared selector, unchanged across domains, choosing among domain-written candidate sets, beats the
  standard method in seven of ten real domains under the pre-registered rule (biology undecided on 6 of 8 cells), and in four after a
  Holm correction across units. The full seed's results in AI agents, AI-to-human replies, inventory and satellite
  downlink replicate on fresh cells with the AI-agent leak fixed (STRUCT1).
- **Confirmed (§5.6):** CONF1 met all its pre-registered criteria in 4 domains (p < 1e-5); CONF3 met them
  for the communication principle (3 AI rows, p < 1e-7) and for moves composed in the RSOS language (3 of 4 rows; with
  the qualifications in §5.6), and met them in 4 of 5 rows for the cross-domain claim.
- **Not claimed:**
  - the best method in any field;
  - that the selector alone, without its domain-written candidates, produces the gains: STRUCT1 tested this under
    seal, and it does not (level NOT SHOWN);
  - production-scale savings, or any market-wide figure;
  - anything about physics or cosmology.
- **Not shown:** neural sensing and quantum measurement. The seed did not beat the separately implemented stronger
  method in energy or inventory. The comparisons with stronger methods in AI agents and satellite downlink carry the
  qualifications in §5.1 and §7.

## 2. The seed: a shared selector and domain-written candidates
**Shared, unchanged across domains** (`real/seed3.py`, mode `seed3v1`): the selector. At every step it takes the
candidates the host offers. It values each one as a whole plan over the horizon in the unit's own predicted futures,
read from the host's own model or real past and never from the real future. It takes the best candidate only if it is
at least as good as the standard action in the same futures (the membrane). Where the resource is free, value is
lexicographic: result first, then less resource. It also fixes an order of candidate families (VAKOG), keeps a shared
trace, and has an observer that switches a candidate family off for a few steps when it does not serve.

**Written per domain** (`real/hosts/<domain>.py`, functions `branches`, `primitives` and `frame`):
- the candidates: present (the standard action); own past and planned actions; actions focused on one part; coupled
  actions on parts that drive each other;
- library patterns P1–P8; P4P5 is the stronger method's own action, where one exists;
- frame levers. Examples:
  - `F:blind` in AI agents: one planner call writes the whole tool plan, and a deterministic runtime executes it;
  - `F:reuse`: reuse an earlier plan of the same shape;
  - compact-state prompts (`F:holo`) and "mention" slots in AI-to-human replies.

These candidate sets carry most of the domain knowledge. They were revised on development cells before the seal; for
example, the satellite host replaced a value-per-MB rule, and the AI-to-human host was revised on 24 Nov. Every revision
was made before the seal and is recorded in the host file headers and `real/quick_logs/`. REAL1 used an earlier,
simpler selector (`real/seed.py` at commit `0e83e83`) with candidates of the first kind only.

## 3. Domains and baselines

| Domain | Real host | Standard method | Stronger method (REAL3) | Resource |
|---|---|---|---|---|
| AI agents | gpt-oss-20b, Llama 3.1 8B (REAL1b: Llama 4 Scout) via OpenRouter; tool tasks | ReAct; self-consistency | early-stopping self-consistency with a calibrated per-state reliability posterior (CGES-style; no token log-probabilities) | kilotokens per cell (4 tasks) |
| AI–AI messaging | a 4-hop question over 60 facts split between two real models; messages of at most K = 2 facts per round, selected by rule; the models answer | a rule-based relevance summariser (the K most relevant unsent facts per round) | = standard | message tokens (characters / 4) |
| AI–human replies | real Topical-Chat conversations, real model replies | direct reply | = standard | kilotokens per 8-reply episode |
| Quantum measurement | Qiskit circuits, Aer simulator | Neyman shot allocation | = standard | shots |
| Satellite downlink | real orbits (CelesTrak, Skyfield), real contact windows; data arrivals synthetic (Poisson) | value-per-MB priority queue | exact look-ahead MILP over the current queue (no model of future arrivals) | contact capacity |
| Energy | real solar (pvlib TMY3), real household load (UCI) | rule-based time-of-use dispatch | scenario-based stochastic MPC | battery wear |
| Inventory | real Walmart weekly sales (Kaggle, 7 series) | base-stock policy | scenario-based stochastic LP with the capital budget | capital |
| Robotics | Gymnasium pendulum physics | energy swing-up + LQR | none | control effort |
| Neural sensing | real recording, DANDI 000140 | greedy Kalman sensor selection | none | samples read |
| Classification ("life science") | the ORG-REAL1 hosts; 2 of their 4 datasets are biological | best single method of ORG-REAL1 | none | labels |

## 4. Design and integrity
- **Pre-registered and fingerprinted.** Code and pass rules were hashed and pushed before each run:
  - REAL1: `real/PREREG_REAL1.md`, `real/SEAL_REAL1.txt`;
  - REAL3: `real/PREREG_REAL3.md`, `real/SEAL_REAL3.txt`, FIX1;
  - SEAL2: `seal2/PREREG_SEAL2.md`;
  - SEAL1: `seal1/PREREG_SEAL1.md`.

  Each machine checks every listed hash and stops on a mismatch. **Not covered by the REAL3 fingerprints:** the data
  files (fetched at run time; the CelesTrak elements were not committed), the agents' task generator and model client
  (`experiments/agents/`), the CGES calibration tree (`ai_agents_tree.json`) and the classification hosts
  (`experiments/sec1/`).
- **Fresh cells.** Development used cells 1–8, REAL1 cells 101–120, and REAL3 cells 201–208 (stage 1) and 209–216
  (stage 2).
  - Neural sensing has 12 recording windows; REAL3 used windows 5–12, one look only. Windows 9–12 had been REAL1's
    fresh windows, but REAL1 produced no neural-sensing result.
  - In satellite downlink the orbit offset repeats every 6 cells, so the 8 REAL3 cells cover 6 orbit geometries, the
    same ones as in development. The on-board data differs per cell.
- **No look-ahead.** The seed's futures come from the host's own model or real past.
- **Paired cells, with an independence breach in AI agents.** Each cell runs every method on the same cell data.
  - Model sampling (temperature 0.7) is not seeded, so the draws are not identical.
  - The REAL3 unit clears the selector's trace between jobs. But it runs four jobs in two reused worker processes
    (`cloud/real3_unit.py`), and three module-level stores in `real/hosts/ai_agents_blind.py` are never cleared:
    `PLAN_POOL` (plans reused by `F:reuse`), `EXEC` and `TRACE`. A later AI-agent job could therefore reuse plans and
    statistics from an earlier cell or unit.
  - `F:reuse` fired in 8 of 8 gpt-oss self-consistency cells and 5 of 8 ReAct cells. This is consistent with leakage
    but does not prove it.
  - Until the AI-agent units are re-run with the stores cleared per job, their intervals assume an independence that
    did not fully hold. Other domains do not use these stores.
- **Pass rules (REAL3).** Two looks, Bonferroni: two-sided 97.5 % paired-t intervals.
  - Priced and fixed-budget units are SHOWN if mean result gain > 0 and the lower bound > 0.
  - Free-resource units are SHOWN if mean resource saved > 0 with lower bound > 0, and the result is not worse: mean
    gain ≥ 0, or its lower bound ≥ −2 % of the standard's mean. This is a weak guard: any non-negative mean passes,
    however wide the interval.
  - After stage 1, a unit is SHOWN, NOT SHOWN (upper bound ≤ 0), or UNDECIDED and goes to stage 2.
  - Stage 2 is assigned per row and model, not per unit, so a unit already SHOWN can receive stage-2 cells. The
    sealed analysis then reports it on all 16 cells.
  - The analysis code also has a futility clause for free rows that the pre-registration does not state; it changed
    no decision.
  - A domain counts if any of its units is SHOWN. **No correction across units or domains was pre-registered** (see
    §5.1, multiplicity).
- **Seed version chosen by a fixed rule.** A version with all RSOS operators (v2) was built. The rule was: use v2 only
  if it wins more development row-cells than v1. The rule was applied to the finished development cells; the second
  development wave was stopped early to save budget. v2 did not win more, so v1 was sealed.

## 5. Results, layer 1: real tools, real data, real models

### 5.1 REAL3 (main confirmatory run)
Source: [`real/RESULTS_REAL3.md`](../real/RESULTS_REAL3.md) (sealed script output; the convention used here: all cells
the unit received), [`real/RESULTS_REAL3_SUMMARY.md`](../real/RESULTS_REAL3_SUMMARY.md); cell files in
`real/results_cloud/real3/`. Intervals are 97.5 %, in the domain's own units (kilotokens per cell for AI agents,
kilotokens per episode for AI–human, tokens per episode for AI–AI, result units otherwise). Percentages are relative to
the standard's mean.

| Domain, unit | Status | Cells | Against the standard | Against the stronger method |
|---|---|---|---|---|
| AI agents, gpt-oss-20b, ReAct | SHOWN | 8 | 51.3 % fewer tokens (+1.99, +9.57); accuracy +0.16 (+0.03, +0.29) | 74.0 % fewer tokens; accuracy +0.06 (−0.12, +0.24); see note b |
| AI agents, gpt-oss-20b, self-consistency | SHOWN | 8 | 68.4 % fewer tokens (+13.6, +23.1); accuracy +0.06 (−0.16, +0.29) | 56.3 % fewer tokens; accuracy +0.09 (−0.09, +0.28) |
| AI agents, Llama 3.1 8B, self-consistency | SHOWN (stage 1; note a) | 16 | 46.5 % fewer tokens (+12.9, +31.1), 13/16 | 40.0 % (16 cells); not shown on the 8 deciding cells |
| AI agents, Llama 3.1 8B, ReAct | SHOWN (stage 2; note a) | 16 | 25.4 % fewer tokens (+0.32, +13.0) | 43.9 % (16 cells); not shown on its 8 stage-2 cells |
| AI–AI messaging | SHOWN | 8 | 36.9 % fewer tokens (+91, +2,680); both methods answered every question (ceiling) | – |
| AI–human, Llama 3.1 8B | SHOWN | 8 | 41.0 % fewer tokens (+0.44, +0.97); proxy +0.10 (−0.09, +0.29) | – |
| AI–human, Mistral Small 3.2 | SHOWN | 8 | 43.6 % fewer tokens (+0.37, +0.83); proxy +0.28 (+0.03, +0.53) | – |
| Inventory | SHOWN | 8 | +1.36 % (+20.7, +45.8), 8/8 | +0.00 % (−1.78, +1.86), 3/8 |
| Energy | SHOWN (stage 2) | 16 | +5.79 % (+0.12, +1.12), 12/16 | −1.53 % (−0.37, +0.01), 4/16 |
| Satellite downlink | SHOWN | 8 | +1.50 % (+4.35, +9.92), 8/8 | +0.89 % (+0.33, +8.18), 8/8; see note c |
| Robotics | SHOWN | 8 | 14.3 % less control effort (+3.28, +18.9), result +1.80 % (+0.48, +5.52) | – |
| Quantum measurement | NOT SHOWN | 16 | −0.39 % (−0.0096, +0.0020), 6/16 | – |
| Neural sensing | NOT SHOWN | 8 | +5.85 % (−0.015, +0.030), 4/8 | – |
| Classification | UNDECIDED | 6 of 8 | 5/6 cells; accuracy +5.1 % (−0.032, +0.119) with 90.9 % fewer labels; one pair timed out, not re-run | – |

**Notes.**
- **a. Llama 3.1 8B agents: the baseline barely works.** The standard methods reached 0.047 accuracy over 32 cells and
  0 of 32 tasks on every stage-2 cell. In stage 1, the standard ReAct arm had 2–4 failed API calls per cell, and two
  cells logged no tokens for the standard (a provider failure). Token savings against a baseline this weak say little.
  These two units are reported but do not carry the AI-agent claim, which rests on gpt-oss-20b. The self-consistency
  unit was decided at stage 1 (50.5 % fewer tokens on cells 201–208); its 8 stage-2 cells, run because stage 2 is
  assigned per row and model, gave 42.6 %.
- **b. What beats CGES in AI agents is mainly an architecture change.** In gpt-oss cells the seed chose the stronger
  method's own action (P4P5) 0–1 times per cell. It chose the plan-then-execute lever `F:blind` 73 times in total, and
  `F:reuse` 11 times. The comparison is therefore between plan-then-execute selected by the seed and a sampling method.
  For the ReAct units, CGES uses about twice the standard's tokens (21.1 vs 11.3 kilotokens per cell), which inflates
  "74 % fewer than the stronger method". The same CGES baseline was run in both units and gives different numbers
  (21.1 vs 19.5 kilotokens; accuracy 0.875 vs 0.813): this is run-to-run noise.
- **c. Satellite downlink: unequal information and compute.** The MILP plans only on the current queue. The seed holds
  the MILP's action as a candidate and also rolls out sampled future arrivals (about 25 rollouts × 3 samples × 6 passes
  per decision). The fair stronger opponent is a scenario MILP. Compute was not recorded for any method.
- **AI–human scores a proxy the seed targets.** The score is the overlap of the reply's content words with the next
  human turn. The seed's candidates include "mention" slots filled with words a corpus model predicts will recur, so the
  proxy gains are not evidence of better replies. The token savings stand; reply quality was not measured.
- **Accuracy.** "Accuracy not worse" is a weak statement here. Several accuracy intervals span about ±0.2 (table).

**Count and multiplicity.**
- **Pre-registered rule: seven of ten domains SHOWN against the standard; biology undecided (6 of 8 cells).**
- The rule controls error per unit only. A Holm correction at family-wise 2.5 % over the 13 decided units (one-sided
  p, doubled for the two looks) keeps four domains: AI agents (gpt-oss), AI–human, inventory, satellite downlink.
  Robotics (p = 0.0050 against a threshold of 0.0042), energy (0.0078 against 0.0050) and AI–AI (0.019) drop out.
  Recomputation: Appendix A.

### 5.2 REAL1 and REAL1b (earlier selector)
Source: [`real/results_cloud/RESULTS_REAL1.md`](../real/results_cloud/RESULTS_REAL1.md),
[`RESULTS_REAL1B.md`](../real/results_cloud/RESULTS_REAL1B.md). 20 fresh cells per unit, 95 % intervals, earlier
selector with candidates of the first kind only (no frame levers).
- REAL1 SHOWN in six domains:
  - AI–AI: 13.0 % fewer tokens;
  - AI–human with Llama: 1.3 % fewer tokens;
  - classification: +7.8 %;
  - inventory: +0.6 %, 20/20;
  - energy: +7.8 %, 18/20;
  - satellite downlink: +1.2 %, 20/20.
- Not shown: AI agents on gpt-oss-20b (self-consistency saved 47.1 % of tokens, but mean accuracy was −0.0125, so the
  unit failed the guard); quantum; robotics. AI–human with Mistral was not shown, though the domain was. There is no
  REAL1 result for neural sensing, and the Llama 3.1 8B agent jobs crashed.
- REAL1b, a sealed addendum: AI agents on Llama 4 Scout, self-consistency, SHOWN (42.7 % fewer tokens, accuracy
  +0.01). It is a separate follow-up with its own pre-registration. It is not added to REAL1's count here.

From REAL1 to REAL3: AI agents (gpt-oss) and robotics moved to SHOWN. AI–human stayed SHOWN, with token savings rising
from 1 % to 41–44 % once frame levers were added. Inventory's margin rose (+0.6 % to +1.4 %), and energy's fell (+7.8 %
to +5.8 %). Classification is undecided: better in 5 of 6 cells with 90.9 % fewer labels, but its interval includes zero. Quantum stayed not shown. The near-identical token savings of REAL1 gpt-oss
self-consistency (failed at −0.0125 accuracy) and REAL1b Llama 4 Scout (passed at +0.0125) show how the
non-inferiority guard acts as a near coin-flip on accuracy.

### 5.3 Blind planning (earlier, separately sealed)
Source: [`README_PUBLIC.md`](../README_PUBLIC.md) and the RSOS Language whitepaper (doi:10.5281/zenodo.24304403).
A planner model names only which state keys change; a deterministic runtime computes every value.
- 256 of 256 tasks were exact across six models from four providers. The strongest one-call JSON Patch pattern built
  for comparison failed on one request type.
- Against one model call per step, blind planning used 2.2–2.4 calls per task instead of 42–43.
- Cost per correct task at 300 keys was 0.45–0.61 times the JSON Patch comparison.

The AI-agent lever `F:blind` in REAL3 applies the same plan-then-execute principle.

### 5.4 STRUCT1: the structure alone, an ablation (sealed)
Source: [`real/PREREG_STRUCT1.md`](../real/PREREG_STRUCT1.md) and its
[addendum](../real/PREREG_STRUCT1_ADDENDUM.md) (the exact candidate sets; written after the start, before any result),
[`real/SEAL_STRUCT1.txt`](../real/SEAL_STRUCT1.txt) (51 files, including the committed data),
[`real/results_cloud/struct1/RESULTS_STRUCT1.md`](../real/results_cloud/struct1/RESULTS_STRUCT1.md); run 45596832492,
sealed at commit `925abf5`.
- **Question:** does the general structure carry without the domain-written levers? The arm "structure" is the
  sealed REAL3 seed with `primitives` and `frame` switched off. It keeps:
  - own-future valuation;
  - time branches;
  - the own-plan continuation;
  - Law 4 landing or the whole;
  - the membrane;
  - the observer.

  It chooses from the same native branches as plain rollout. The other arms were the full seed, plain rollout, the
  standard and the strongest method.
- **Design:** fresh cells 301–308; five rows (AI agents on gpt-oss-20b with two standards, AI–human on Mistral, AI–AI,
  inventory, satellite); one look. Holm over all 12 primary tests (structure vs standard and vs rollout per unit).
  Criteria fixed before the run: all met if at least 4 of 5 rows pass both tests, partly for 2–3 rows, not met
  for fewer than 2.
- **Leak fix:** the plan stores and the seed trace were cleared before every arm, and every cell ran in its own process.

**Level reached: NOT SHOWN (0 of 5 rows).**

| Row | Structure vs standard | Structure vs plain rollout | Full seed vs standard | Full seed vs strongest |
|---|---|---|---|---|
| AI agents, ReAct | 5.7 % fewer tokens, n.s.; accuracy −0.03 | −1.6 %, n.s. | 45.1 % fewer tokens, accuracy +0.19 | 63.6 % fewer tokens (CGES), accuracy +0.09 |
| AI agents, self-consistency | 42.0 % fewer tokens, but accuracy −0.03 fails the guard | +0.5 %, n.s. | 57.3 % fewer tokens, accuracy +0.19 | 45.6 % fewer tokens (CGES), accuracy +0.09 |
| AI–AI | 10.6 %, n.s. | 6.6 %, n.s. | 13.0 %, n.s. | – |
| AI–human (Mistral) | 1.7 % fewer tokens, not significant after Holm | +0.2 %, n.s. | 43.3 % fewer tokens, proxy +0.12 | – |
| Inventory | +0.72 % (passes) | +0.09 %, n.s. | +1.26 % | +0.02 %, n.s. |
| Satellite downlink | +0.93 % (passes) | +0.34 %, n.s. | +1.33 % | +1.21 % (MILP) |

n.s. = not significant (one-sided p > 0.05 before correction). Structure vs full seed: worse in every row (AI agents
−36 % to −72 % tokens, AI–human −73 %, inventory −0.54 %, satellite −0.40 %).

**What it shows.**
- **Ablation.** The general structure alone performs like plain rollout. Where it beats the standard (inventory,
  satellite), plain rollout does too (+0.63 %, +0.58 %). The gains of the full seed come from the domain-written
  candidates, which answers the reviewer's first question with sealed data.
- **Replication.** The full seed's REAL3 results replicate on fresh cells with the leak fixed: AI agents, AI–human,
  inventory and satellite against the standard; AI agents and satellite against the stronger method.

### 5.5 Operator lineage: every lever the full seed uses, traced to the RSOS operator language
The levers that carry the full seed's gains (STRUCT1, §5.4) are host-written moves. Each host names the RSOS operator a
lever implements in its own `op_of()` table, written before CONF1 and CONF2 (`real/hosts/<row>.py`); the seed's shared
table is `COMMON` in `real/seed3_ops.py`. The table below lists the levers the full seed chose on fresh cells (uses from
STRUCT1 and CONF1; final counts in `RESULTS_CONF2.md`), with the operator, where the operator sits in the structural map
(`map/STRUCTURAL_MAP_22NOV.md`) and the code.

| Row | Lever (family) | What it does in the domain | RSOS operator | Place in the structural map | Code |
|---|---|---|---|---|---|
| AI agents | `F:blind` | one planner call names the keys that change; a deterministic runtime computes every value | COMPRESS (many into one) | language U8 "many into one symbol"; Part K.10 hologram coding | `real/hosts/ai_agents.py` `frame()`, `OPS_OF`; `real/hosts/ai_agents_blind.py` |
| AI agents | `F:reuse` | reuse a confirmed plan of the same shape at no model call | INHERIT (the trace) | Part I.4 combinations, J.3 Row D "INHERIT (the trace)" | `ai_agents.py` `OPS_OF` |
| AI agents | `P4P5` (CGES stop) | the stronger method's stopping rule offered as one candidate | FUSE (joint choice, P4) | Part I.2 primitives P4/P5 | `real/seed3_ops.py` `COMMON` |
| AI–human | `F:holo`, `F:holomin` | a compact state of the whole conversation instead of the history | COMPRESS | U8; Part K.10 | `real/hosts/ai_human.py` `OPS_OF` |
| AI–AI | `F:holo`, `F:holokey` | a message that carries structure the receiver computes from | COMPRESS | U8; Part K.10 | `real/hosts/ai_ai.py` `OPS_OF` |
| Inventory | `P4P5:stochastic_lp` | the scenario LP's order as one candidate | FUSE | Part I.2 P4/P5 | `real/hosts/economics.py` `OPMAP` |
| Inventory | `F:otrace:lp_corrected` | the LP corrected by the observed trace | HEAL | Part H "heal without harm" | `economics.py` `OPMAP` |
| Inventory | `F:pool:capital_newsvendor` | capital pooled across items | FUSE | U60 | `economics.py` `OPMAP` |
| Satellite | `F:holo-carry`, `F:holo-plan` | the pass tail carries a coded fragment of the backlog to later passes | CARRY | Part K.10 "the whole carries the whole" | `real/hosts/space.py` `op_of` |
| Satellite | `P4P5:exact-planner` | the look-ahead MILP's plan as one candidate | FUSE | Part I.2 P4/P5 | `space.py`; `COMMON` |

Native actions of a host (for example AI agents' `stop` = commit early, AI–human `unit`/`top` = mention slots) are the
domain's own options, shared with plain rollout; they are listed with their mapping where one exists (`stop` has none).
**What the lineage shows and does not show:** each winning lever has a named operator and a place in the map, assigned
by the hosts before these runs. The mapping is a naming made by the authors, not an independent test; whether the
operator language alone produces such levers is tested by the generated arm (CONF1, CONF2: claim 3).

### 5.6 Confirmations on fresh cells: CONF1, CONF2, CONF3
Each was pre-registered with levels fixed before the run (`real/PREREG_CONF1.md` with seals A, B and the FIX1 addendum;
`real/PREREG_CONF2.md`; `real/PREREG_CONF3.md`); seal commits and push times are in `HANDOFF_STRATEGIC.md`. Results:
`real/RESULTS_CONF1.md`, `RESULTS_CONF2.md`, `RESULTS_CONF3.md`. One-sided paired t, Holm within each family; AI rows
are decided on tokens with a result guard. The leak fix of STRUCT1 applies throughout.

| Test | Cells | Claim | Pre-registered criteria | Key numbers (full seed vs standard unless stated) |
|---|---|---|---|---|
| CONF1 | AI agents 40, AI–human 38, inventory 12, satellite 12 | full seed beats the standard in all 4 domains at Holm p < 1e-5, all levers traced | **all criteria met** | AI agents 58–69 % fewer tokens, accuracy +0.11/+0.15 (p 8e-11, 5e-27); AI–human 42 % (5e-21); inventory +1.42 %, 12/12 (1e-9); satellite +1.67 %, 12/12 (1e-9), +1.33 % over the MILP |
| CONF2 | + AI–AI 40, satellite generated 12 | 1 cross-domain (5 rows) / 2 communication / 3 one-move-per-operator generated | partly / partly / not met | AI–AI 28 % fewer tokens (p 4.6e-4); generated: satellite +1.45 %, 12/12 (1.4e-4) |
| CONF3 | AI agents 40, AI–human 40, AI–AI 150, inventory 12, satellite 11 + 23 composed | 1 cross-domain / 2 communication / 3 composed operator chains | partly / **all met** / **all met** | tokens: AI agents 48–61 % (p 8e-9, 2e-21), AI–human 42 % (8e-25), AI–AI 25 % on 150 cells (1e-9); inventory +1.34 % (p 1.4e-5, just above 1e-5); satellite +1.98 % (1e-6); composed: AI agents self-consistency 45 % fewer tokens (2e-23), AI–AI 27 % (8e-12), satellite +1.01 %, 22/23 (1e-7); AI–human not passed |

**Disclosures.**
- CONF1 satellite first failed in all jobs because CelesTrak returned HTTP 503; the orbit elements were then frozen once,
  committed and fingerprinted, and the jobs re-ran on that file (FIX1 addendum).
- Inventory moved from the workspace to the cloud before any result was read.
- Topical-Chat has 539 test conversations, so AI–human cells 539–540 do not exist (CONF1 has 38 cells; CONF3 uses
  401–440).
- CONF3 satellite cell 706 timed out at 180 min (11 full-seed cells, 23 composed).
- CONF3 was designed after the interim CONF1/CONF2 results; all three are reported, and none replaces another.
- CONF2's one-move-per-operator design was a drift from the RSOS grammar (composition); CONF3's composed arm corrects it.

**How to read claim 3.**
- The composed moves (operator chains such as `see>trace>compress>inherit>contain>act`) were written by a fresh agent
  from the RSOS sources and a short domain description, and sealed as written.
- They carried the gain where they were chosen: satellite (87 % of choices) and AI–AI (45 %, equal to the full seed).
- In AI agents, self-consistency, they were chosen in only 4 % of decisions; that row's gain comes mostly from the
  shared structure and the host's native actions, as in STRUCT1.
- A control agent given the same domain descriptions without the RSOS sources has not been run. Until it is, the
  result shows that moves written in the language win in two domains, not that the language rather than a capable
  model produced them.

### 5.7 Against RSOS-free planning, and what carries the gain: CONF4, ABL1, CONF5, CONF6
Pre-registrations: `real/PREREG_CONF4.md`, `PREREG_ABL1.md`, `PREREG_CONF5.md`, `PREREG_CONF6.md`; screens on development
cells only (never reused): `real/pilot/PILOT1_NOTES.md`, `PILOT2_NOTES.md`. Results: `real/RESULTS_CONF4.md`, `RESULTS_ABL1.md`,
`RESULTS_CONF5.md`, `RESULTS_CONF6.md`. Each seal was committed and pushed before its first cell (commits and push times in
`HANDOFF_STRATEGIC.md`). All runs had no crash and no re-run, except the PILOT1 AI-agent screen (an import-order crash,
re-run after the fix and disclosed). Layer colour: the layer-2 structure runs unchanged on layer-1 data (cyan).

| Test | Question | Cells | Pre-registered criteria | Key numbers |
|---|---|---|---|---|
| CONF4 | do programs written by an AI given the RSOS sources beat programs by the same AI without them? (3 + 3 fresh agents; both sides given the same compiled operator channels) | AI agents 40, AI–human 40, AI–AI 150, satellite 24 | NOT SHOWN (1 of 4 rows) | AI agents (ReAct): 6.7k vs 12.0k tokens (−44 %), accuracy 0.93 vs 0.91, Holm p 4.9e-16, 39/40; other rows no difference |
| ABL1 | does switching off one operator cost the gain? | AI agents 40, AI–AI 150, satellite 48 | NOT SHOWN (0 of 3) | full RSOS beat the standard in every row (p 1e-25, 3e-16, 2e-15), but the operators switched off were barely chosen; see disclosures |
| CONF5 | does the RSOS structure identified per host (PILOT1) beat **plain rollout**? | AI agents 48, AI–AI 100, satellite 20 | **met in 2 of 3 rows** | AI agents, full RSOS (v2 operator layer + persistent trace + composed programs): 7.3k vs 12.9k tokens (−43 %), accuracy 0.95 vs 0.83, Holm p 1.9e-13, 44/48. Satellite, seed v1: +0.74 %, 20/20, p 1.5e-8. AI–AI: tokens −3.8 % (p 0.25, not passed); accuracy 0.73 vs 0.59 (reported only) |
| CONF6 | with the **whole** AI–AI system bound to one structure (PILOT2), does RSOS beat plain rollout on accuracy and on tokens? | AI–AI 200 | **all criteria met** | accuracy 1.000 vs 0.875 (25 better, 0 worse; Holm p 1.3e-7); tokens 1,286 vs 2,645 (−51 %, 180/200, p 5.1e-28); Law 0 held |

**What the whole-system binding is (CONF6).** In CONF5, RSOS chose only agent A's messages and B ran the standard, so the
seed had to model B's future with a rule. In CONF6: (1) B is shaped by the same structure: it sends first the facts it
holds on the question's four-hop chain as far as its own view allows, and the facts A asked for by key; (2) the system
checks itself, as a law in law form (invariant: commit only on a complete chain; check: walk the chain in the agent's own
view; response: continue). The models still write every answer and all tokens are counted. The completeness check is a
deterministic computation on the agent's own facts (Law 2); plain rollout does not have it, by design. Secondary
readings: whole vs RSOS-on-A-only +7.5 points and −47 % tokens; hologram switched off: no difference (p 0.16 and 0.48),
so the gain is carried by binding the whole system, not by the hologram message. The test does not separate its two parts.
Measured but not pre-registered: the whole-system arm took 1.6 s per cell against plain rollout's 3.0 s (faster in 141 of 200).

**Which RSOS operators the seed actually chose (CONF5 logs).**

| Host | Most-chosen operator families | Share of decisions |
|---|---|---|
| AI agents (full) | landing / stop in the unit's own future 19 %; blind plan (Law 2) 17 %; FUSE, OVERLAY, ENTER inside the Owl room 22 %; past options 6 % | operators passing the Law 0 membrane: FUSE 923, PIERCE 782, BEAM 767/755, ENTER 761, ZOOM 710, HEAL 694, OVERLAY 397, RE-HOST 345 |
| Satellite (v1) | hologram plan with CARRY of a fragment into the next pass 84 %; library exact planner (P4/P5) 5 %; BEAM (`focus_science`) 3 % | |
| AI–AI (v1) | hologram with vote 46 %; hologram with key 20 %; library joint (P4/P5) 7 %; White Dragon repair (P3) 4 % | |

**Disclosures.**
- CONF4's control agents received the same compiled operator channels (blind plan, hologram, key) as the RSOS agents, so
  CONF4 measured what the RSOS source text adds on top of operators already compiled into both arms, not RSOS against no
  RSOS. An earlier reading ("the gains come from the engine and channels, not the language") was a drift: the engine and
  channels are compiled RSOS operators.
- ABL1 chose one operator per row from earlier effect sizes without checking its use; the programs barely chose them, and
  the host's native branches, which map to the same operators, stayed on. ABL1 shows those single switches were not the
  cause; it does not show that the operators are inactive. CONF5's logs show the hologram family carrying 78–84 % of
  decisions in two rows, with the host levers on.
- Plain rollout uses the hosts' native options, several of which map to RSOS operators; what it lacks is the seed
  (membrane, landing, library, valuation in the unit's own future, operator layer, trace) and, in CONF6, the
  whole-system binding.
- CONF5's satellite cells take 30–65 minutes each (seed v1); its AI–AI cell counts came from an 8-cell screen whose cells
  were easier than the fresh ones, which is why its token effect did not carry over.

## 6. Results, layer 2: a controlled simulated world
Layer 2 is a simulated world built for this work, where the structure was developed before it was bound to real
hosts. Its results hold for that world only.
- **SEAL2** ([`seal2/RESULTS_SEAL2_cloud.md`](../seal2/RESULTS_SEAL2_cloud.md), fresh seeds, 22 cells each):
  - Meaning: the structure beat the best single room in 22 of 22 cells.
  - D: a child unit beat its best parent in 20 of 22.
  - E: the structure beat the best native method in 22 of 22.
  - The laws-as-mathematics row did not pass: L3 (14 of 22) and L5 (7 of 11) fell below 90 %.
- **SEAL1** ([`seal1/RESULTS_SEAL1.md`](../seal1/RESULTS_SEAL1.md)): 13 of 15 rows passed.
  - Road 8, the first beam: 18 of 18 cells.
  - The 12 earlier rows passed their re-check: 21 of 21 shades.
  - Road 10 (partners) did not pass: joining beat working alone in 10 of 10, but every partner was at least as well off
    as alone in only 9 of 10.
  - Laws as mathematics did not pass: L3, L5 and LE fell short, and the noise-free Law 4 check reached precision
    ≥ 0.90 in 8 of 11 shades (10 required).

## 7. Prior art and the reviewer's first questions
Source: [`real/PRIOR_ART_REAL.md`](../real/PRIOR_ART_REAL.md), a ten-query web search made on 24 Nov for REAL1, before
the frame levers existed. It is not exhaustive and does not yet cover the parts that drive the REAL3 gains.
- **Rollout and scenario MPC.** Valuing options over a base policy's futures, with the base as a floor, is rollout
  (Bertsekas; Bertsekas, Tsitsiklis and Wu, 1997). Its cost-improvement property guarantees no worse than the base.
  Scenarios from historical data are standard in stochastic MPC.
- **Plan reuse.** MPC warm start, AC4MPC, MPPI warm-start buffers.
- **Inheritance between policies.** Genetic Policy Optimization, PDERL.
- **Agent token savings.** Adaptive and early-stopping self-consistency (ASC, ESC, CGES, ReASC).
- **Not yet searched; known families that likely cover the frame levers:**
  - plan-then-execute agents (for example ReWOO, LLMCompiler, Plan-and-Solve) for `F:blind`;
  - prompt and context compression (for example LLMLingua, summarised memory) for compact-state prompts;
  - stochastic or scenario MILP for downlink.

  A new search is required before publication. Until then, no part of the candidate sets is claimed as new.
- **Updated search, 26 Nov** ([`paper/PRIOR_ART_26NOV.md`](PRIOR_ART_26NOV.md), four searches, not exhaustive):
  - receiver-relative messaging has a close relative: "receiver-relative bounded coordination" (NeurIPS 2026,
    arXiv 2610.03769), plus action-state and multi-order agent communication (2026);
  - answering only on sufficient evidence: R2-KG abstention, PAR2-RAG sufficiency checks, skill programs that verify
    completeness (2025–2026);
  - perspective as a first-class part of an agent architecture: the Observer–Situation Lattice (2026);
  - operators reused across domains: domain-independent planning; operads for system design.
- **What is not found so far:** one operator language bound unchanged onto LLM agents, an AI–AI channel and a satellite
  scheduler, sealed against each host's standard and against plain rollout; and the same selector across ten real
  domains under one discipline.

Reviewer questions, answered:
1. *Doesn't rollout's improvement guarantee predict a win over the standard?* Yes. STRUCT1 tested it under seal: the
   general structure without the domain-written levers is not distinguishable from plain rollout in any of five rows
   (§5.4). The gains come from the domain-written candidates. The claim is therefore about a sealed discipline that
   selects among them, replicated on fresh cells, not about the structure alone.
2. *Standard versus best in field.* The claim is against each field's standard.
   - In AI agents the stronger comparison is plan-then-execute against a sampling method (note b).
   - In satellite downlink, it is MILP plus stochastic look-ahead against deterministic MILP (note c).
   - In energy and inventory the seed had the stronger method's action as a candidate and still lost or tied.
3. *The fixes.* All are listed in §8.
4. *In CONF6 a completeness check decides when to answer; isn't accuracy 1.000 just that check?* Partly, and it is
   disclosed. The check walks the chain in the agent's own facts (Law 2: the runtime computes, the model writes); the
   models still write every answer. Plain rollout lacks it by design, because it is RSOS structure. The same binding also
   cut tokens by 51 %, which a completeness check alone does not do: B sending its part of the chain first is what
   shortens the exchange. CONF6 does not separate the two parts; that is a named next test (§10, 3c).
5. *Small open models and synthetic tasks.* True: gpt-oss-20b, Llama 3.1 8B and Mistral Small 3.2, on a synthetic
   AI–AI task and RSOS's own agent tasks. Frontier models and harder public benchmarks are the next tests, against the
   strongest planner–executor patterns in use.
6. *These mechanisms already exist.* Each has relatives (§7, updated search). The claim is one operator language bound
   unchanged across unrelated hosts and sealed against each host's standard and against plain rollout.
7. *A small team graded its own work.* Every test was sealed before it ran, every test whose criteria were not met is
   reported, and every table rebuilds with one command. Independent replication is what settles it; the open record
   (§11) is built for it.

## 8. Limits and disclosures
**Limits**
- The selector is shared; the candidate sets are written per domain and were revised on development cells (§2).
- Four domains use real data and real physics on simulated devices (quantum, energy, inventory, robotics). Satellite
  data arrivals are synthetic (Poisson). The AI–AI task is synthetic and rule-messaged.
- AI–human scores a word-overlap proxy that the seed's candidates target (§5.1); no live people took part.
- The Llama 3.1 8B agent baseline is near zero accuracy (§5.1, note a).
- Compute is not matched in any domain. Wall-clock time per cell is recorded from CONF5 on, but not pre-registered.
- Fixed-budget domains are judged on result only. In those domains the seed used more of the logged resource column:
  satellite downlink 13.5 % more contact capacity in REAL3 (10.0 % in REAL1), inventory 3.5 % more capital in REAL3.
- No multiplicity control across units or domains was pre-registered (§5.1).
- REAL3 has 8–16 cells per unit; real models vary from run to run on the same cell.
- The REAL3 fingerprints do not cover data or several dependencies (§4).
- All runs were made by one team in two days. Independent replication is the test that matters.

**Disclosed fixes and errors**
- After REAL1 ran, `real/seed.py` and every REAL1 host file were edited for REAL2 and REAL3. REAL1 ran on the sealed
  commit `0e83e83` and stands. Its fingerprint check passes only at that commit; at the current head, 22 files differ.
  New versions now get new file names.
- REAL3 FIX1 (commit `7e4b14b`, `real/PREREG_REAL3_FIX1.md`): 5 of 48 stage-1 units crashed on code errors before
  producing a result.
  - Four were classification: the host could not be imported in a worker process. Fixed by setting a path, with no
    code change.
  - One was a Llama agent unit that stopped on a model-written formula that did not parse. Such a formula now counts as
    an invalid plan, like other invalid plans.
  - The units were re-run with no sealed file edited, and stage 2 used the same fixed unit.
- The AI-agent plan stores were not cleared between jobs in REAL3 (§4); STRUCT1 cleared them and the full seed's
  AI-agent results replicated (§5.4).
- SEAL1 FIX1 (commit `baad225`, `seal1/PREREG_SEAL1_FIX1.md`): an unrestored setting made part of the laws step collect
  one arm only. The affected units were re-run with the sealed code and seeds.
- REAL3 fairness decisions made before the seal: quantum joint-setting shots pay their full hardware width; the
  AI–AI message pack is off; classification lands per class.
- SEAL2: the simulated world shares randomness between a world and its forks; LE's check was revised during
  development, each revision sealed before its run.

## 9. How to check it
- REAL3: verify `sha256sum -c` on the hash lines of `real/SEAL_REAL3_FIX1.txt`, which passes at the current head.
  - The table: `cp real/results_cloud/real3/stage*/*.json real/out3/ && python real/analyze_real3.py`.
  - One unit: `PYTHONPATH=experiments/sec1 python cloud/real3_unit_fix1.py <row> <model> <pair> <stage>`.
- REAL1: `git checkout 0e83e83` first; `real/SEAL_REAL1.txt` matches only there. Then run
  `python cloud/real1_unit.py <row> <model> <chunk>` and `python real/analyze_real1.py`.
- SEAL2 and SEAL1: their seal files and `analyze_seal2.py` / `seal1.py analyze`.

- CONF4, ABL1, CONF5, CONF6: `bash reproduce_conf4.sh`, `reproduce_abl1.sh`, `reproduce_conf5.sh`, `reproduce_conf6.sh`
  verify every fingerprint and recompute the tables from the committed outputs; with arguments they re-run cells
  (`space` re-runs the satellite row offline; `mock` checks every CONF6 arm without a model).

AI domains need an OpenRouter key; the other domains run offline after their data-fetch scripts. Seal commits and
run IDs are listed in `real/RESULTS_REAL3_SUMMARY.md`.

## 10. What a stronger test needs (not yet run)
1. Done in STRUCT1 (§5.4): the AI-agent full seed re-run leak-free on fresh cells, the ablation without levers, and
   plain rollout under seal.
2. An ablation per lever family, to say which domain-written candidates carry the gain. (ABL1 tried single operators and missed; the next ablation switches a whole family off from every source, chosen by measured use.)
3a. Done in CONF4 (§5.7): the control without the RSOS sources was run; NOT SHOWN overall, AI agents passed.
3b. Done in CONF5 and CONF6 (§5.7): the full structure against plain rollout under seal.
3c. Next: all three hosts in one sealed test; wall-clock time as a pre-registered measure; the two parts of the
   whole-system binding separated.
3. Fair stronger baselines:
   - plan-then-execute alone (the blind runtime without the seed) in AI agents;
   - scenario MILP in satellite downlink;
   - compute recorded for every method.
4. Fingerprints for data and dependencies, with the exact CelesTrak elements committed.
5. A reply-quality measure for AI–human beyond the word-overlap proxy.
6. A pre-registered multiplicity rule for the cross-domain count.
7. An updated prior-art search (§7).

## 11. The open record: SRC-X.5 (v1.3)

v1.3 renames v1.2 ("RSOS Sealed Claims", RSC). Every rule is unchanged, and every earlier record keeps its id and
its place in the chain. The name SRC-X.5 was first written on 8 June 2025 for a compact key that re-expands into its
full content, which is what a record id is.
Every sealed test in this paper is also a record in an open, append-only, hash-chained log that anyone can check, copy
and add to (`protocol/`, specification `protocol/SPEC.md`). A record states the pass criteria, the fingerprinted files,
the seal time, the run time, the outcome (criteria met: all, partly or not), replications and lineage, and carries no
personal data. One reference file is the node, the command-line tool and the sync; the same admission check runs in
every node, on every laptop and in the public workflow, and a viewer re-checks every record in the reader's browser.
**v1.2: checks, quarantine, supersede and peer audit.** Every record passes seven checks (DISCLOSURE, CONSENT_PRIVACY,
HARM_BOUND, CONFORMANCE, NON_BLOCKING, ATTRIBUTION, PURPOSE), each derived from the governance model of the RSOS
language; each reason names its check. Nothing is prohibited from being submitted: what fails is quarantined with its
reasons, never published, and nothing is deleted. A record is replaced by a modified clone that keeps its identity, and
nodes audit each other with a two-signal rule. Sealed before their confirming runs: 600 of 600 violations quarantined
across 15 classes, every check 30 of 30, 0 of 200 valid records blocked, identity kept through supersede, only the edited
peer flagged, and sync moving only what was missing. Development versions found and fixed three issues before any seal
(a tampered copy reusing a held id answered as admitted; a forecast with a seal dated in the future; a test applying
attribution to pending outcomes).

## 12. What is offered
After approval:
- this paper;
- the open-core seed and hosts under Apache 2.0;
- every sealed cell with its rerun command;
- the sealing method;
- an open benchmark for measuring AI token use against a standard method on one's own workload;
- the SRC-X.5 protocol (an open record of sealed claims): specification, reference node and the open record, for any field.

## Data and licences
Walmart weekly sales (Kaggle competition data), Topical-Chat (Amazon), UCI household power consumption, DANDI 000140,
CelesTrak orbital elements, pvlib TMY3. No third-party data is redistributed. Licence terms and open items:
`DATA_LICENCES.md` in the public release (`public_kit/DATA_LICENCES.md` here).

## Appendix A. Independent review (25 Nov 2026) and how each finding was handled
A separate reviewer, with no access to the development history, checked every number against the result files and
read the host code. Every REAL3, REAL1, REAL1b, SEAL2 and SEAL1 number in revision 1 matched the sealed outputs. Its
findings, and what was done:

| # | Severity | Finding | Handled |
|---|---|---|---|
| 1 | critical | "unchanged, untuned" overstated; gains sit in per-domain candidate sets | reframed: shared selector + domain-written candidates (title, abstract, §1, §2) |
| 2 | critical | Llama 3.1 8B agent baseline near zero accuracy; failed calls | note a; removed from the AI-agent claim |
| 3 | critical | the AI-agent win over CGES is plan-then-execute, not P4P5 | note b; §7 rewritten; ablation and plan-then-execute baseline in §10 |
| 4 | critical | plan stores leak across AI-agent jobs; "same random draws" untrue | disclosed in §4 and §8; re-run in §10 |
| 5 | major | no multiplicity control across units | Holm count added (4 domains); §5.1 |
| 6 | major | stage-1 and 16-cell numbers mixed for Llama | one convention (sealed 16-cell output); stage-1 vs stronger not shown, stated |
| 7 | major | satellite: unequal information and compute vs MILP; 6 repeated geometries | note c, §4, §10 |
| 8 | major | fingerprints do not cover data and dependencies | §4, §8, §10 |
| 9 | major | REAL1 fingerprints fail at head (22 files) | §8, §9 |
| 10 | major | AI–human seed targets its proxy | §5.1, §8, §10 |
| 11 | major | AI–AI described wrongly; ceiling | §3, §5.1 |
| 12 | major | non-inferiority guard is weak | §4, §5.1, §5.2 |
| 13 | major | REAL1 facts wrong in §5.2 | corrected |
| 14 | major | REAL1b timing and count | wording removed; REAL1b not added to REAL1's count |
| 15 | major | prior art out of date for the frame levers | §7; new search in §10 |
| 16 | major | limits incomplete | §8 |
| 17–23 | minor | units; abstract ranges; blind-planning attribution; futility clause; seed-version rule; robotics leads with effort; CGES described and duplicated | corrected (§3, §4, §5.1, §5.3) |
| 24 | minor | biology pending | closed: 6 of 8 cells (one pair timed out at 345 min; no re-run, owner's instruction); UNDECIDED under the sealed rule |

Holm recomputation (one-sided p doubled for two looks; thresholds 0.025/(13−i)): gpt-oss self-consistency, Llama
self-consistency, AI–human Llama, inventory, AI–human Mistral, satellite and gpt-oss ReAct pass. The sequence stops
at robotics (0.0050 > 0.0042).
