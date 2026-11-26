# ENGINE1: the seed evolution engine, first complete run (layer 2), sealed before any engine code

Written 20 Nov 2026, ~06:20 Vilnius. Private. Decision D110. Parts: Ω Root Genome, six children, Father, Mother,
the RSOS operator algebra as generator, Law 0 monitor, champion challenge on a sealed hold-out.

## The module

- **Generator (RSOS operator algebra).** A candidate is a composition of seed primitives with parameters: reading
  through relations (passes, σ multiplier, ε), gate threshold, confidence rule (gap multiplier c), GROW reweighting in
  the reading (on/off), LAND margin and number of land-read rounds, SEE flag mode (gap, disagreement between plain and
  relational reading, their AND / OR). Children compose new candidates from these; the space is not a fixed list.
- **Six children.** Tiger: a new composition across the whole space (10 % of Tiger proposals deliberately leave the
  safe range, so Law 0 is exercised). Lion: one small step from the current best. Leopard: one or two random changes to
  a population member. Bear: replication of a top candidate on fresh calibration scenes. Dragon: fusion of two parents.
  White Dragon: transfer of shared primitives from the best of another target.
- **Father.** Allocates each evaluation to a child by Thompson sampling on that child's measured successes (a success
  = beats the current calibration best; for Bear, a confirmed replication).
- **Mother.** Coverage: every child is used at least 4 times per target; the population keeps the 8 best distinct
  candidates.
- **Ω Root Genome.** Append-only, hash-chained record of every candidate: id, parents, child, target, primitives,
  Law 0 verdict, calibration score, outcome, replication, promotion.
- **Law 0.** Before evaluation, a candidate outside the safe range (passes 1–5, ε 0.001–0.2, σ multiplier 0.25–4,
  thresholds 0–1, margins 0–3, rounds 1–3) is refused and recorded, never run.
- **Champion challenge.** Per target, the best candidate (replicated by Bear when available) is challenged once
  against the incumbent on **hold-out scenes 940–947**, used for nothing else.

## Targets (the three weakest results of tonight)

| Target | Host | Incumbent (tonight) | Score | Promotion margin on hold-out |
|---|---|---|---|---|
| T1 LAND | hologram, 10 % silent flips, no map | O2 rule (margin 1 × std, one round) | recall, valid only if precision ≥ 0.99 | recall + 0.10 |
| T2 heavy damage | hologram, 90 % erasure | LivNRg with the O6 gate (0.9) | exact accuracy | + 2 pp |
| T3 SEE | hologram, 50 % erasure | flag gap < 2·√support | flag precision, valid only if recall ≥ 0.95 | precision + 0.10 |

Calibration scenes 800–803 (search), 804–807 (Bear replication). Budget: 45 evaluations per target.

## Predictions

| # | Prediction |
|---|---|
| E1 | At least one of the three targets promotes a generated candidate on the hold-out |
| E2 (stretch) | All three targets promote |
| E3 | Root Genome: 100 % of candidates recorded with ancestry; the hash chain verifies end to end |
| E4 | Law 0: 100 % of out-of-range candidates refused before evaluation; 0 in-range candidates refused |
| E5 | Father: the child with the most successes receives more evaluations than the median child, on every target |
| E6 | White Dragon (transfer between targets) produces at least one calibration success |

Every prediction reported pass or fail; nothing changed after the run.
