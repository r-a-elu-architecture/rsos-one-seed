# Prior-art search for REAL1/REAL2 (24 Nov 2026, ~19:20-19:40, UTC+02:00). Web search, 10 queries; not exhaustive.

## The seed's parts, each with prior art
| Seed part | Nearest prior art found | Verdict |
|---|---|---|
| Choose by the unit's own future over a base (standard) policy, never worse than it (acceptance guard) | Rollout algorithms (Bertsekas; Bertsekas, Tsitsiklis and Wu 1997): base heuristic + lookahead; cost-improvement property: no worse than the base; broad applications | KNOWN: the seed is a rollout-family method |
| Own planned future actions applied now; own past actions as candidates | MPC warm start by shifting the previous solution (standard); AC4MPC: several initial guesses incl. the shifted previous solution and a policy rollout, the lowest-cost trajectory is applied | KNOWN in parts (shifted plan as candidate); own PAST actions as candidates not found |
| Own committed trajectory (continue the plan one follows) | plan reuse / warm starting in MPC; MPPI warm-start buffers | KNOWN in parts |
| Own future read from the real record (the tree) | scenario-based stochastic MPC with scenarios from historical data / bootstrapping | KNOWN |
| Child inherits both parents' trajectories, beats both | Genetic Policy Optimization (state-space crossover by imitation), PDERL (distillation crossover), behavioural inheritance from parents | KNOWN family; time-shifted trajectory inheritance + own commitment not found as such |
| Agent token savings vs self-consistency | ASC, ESC, CGES (-69.4 % calls, accuracy within 0.06 pts), ReASC (up to -70 %) | KNOWN and STRONGER than our 43-47 % |
| One general method across many domains | DreamerV3 (one configuration, 150+ tasks, outperforms specialists; benchmark tasks); MuZero in video compression (4 % bitrate) and data centres; rollout across many applications | KNOWN as a goal; real-operations cross-domain sealed comparison not found |

## Strongest methods per REAL row (REAL2 opponents)
- Energy: scenario-based stochastic MPC (scenarios from historical data) - the state of the art, stronger than rule-based TOU.
- Satellite downlink: meta-heuristics / MILP planners clearly superior to greedy (e.g. RADARSAT-2 case study; NASA agile EOS MILP planner).
- Economics: stochastic inventory optimisation (dynamic programming / scenario optimisation) beyond base-stock.
- AI agents vs self-consistency: CGES / ReASC-style confidence early stopping.

## What this means
1. Each part of the seed exists in the literature. The seed is, at its core, a rollout / scenario-MPC family method.
2. "Beats standard practice across fields" is largely what rollout theory predicts; it does not by itself support a novelty claim.
3. What is not found: (a) the specific branch set (own past AND own plan AND focused/coupled parts AND own committed trajectory)
   as ONE unchanged structure; (b) a sealed, cross-domain comparison in real operations (10 fields, one hash).
4. Decisive tests for novelty: (i) seed vs PLAIN ROLLOUT with the same base, same scenarios, same budget (does the seed's own
   structure add anything?); (ii) seed vs each field's strongest method (scenario MPC; meta-heuristic/MILP downlink; stochastic
   inventory optimisation; confidence early stopping).
5. Honest claim available now: one unchanged rollout-family structure, sealed, beats standard practice in 7 of 10 real fields.
