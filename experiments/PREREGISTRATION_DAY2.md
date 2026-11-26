# Day 2 pre-registration: re-implementations of C1-EXP-003 and C1-EXP-004

Written and committed **before** the experiments were run. The runtime rules are fixed in `spec/SEMANTICS.md`.
The original ChatGPT code and outputs were never captured (chat 1 records). These are new implementations of the
**recorded designs** (chat 1 T107, T108), on our runtime, so the numbers are not expected to match. Every result is
reported, whichever way it goes.

## R-003 (re-implementation of C1-EXP-003: spatial functional composition)

- 40 worlds (seeds 0–39). Two paintings, each 2 × 4 surface modules with body and sub-code beneath (48 modules).
  Utility measured in an unseen environment (a shifted copy of the training environment), as in the original.
- Conditions: O original (B 2.5 to the right of A); M move B onto A; P pierce B through A without moving; MP move then
  pierce. Interaction I = U(MP) − U(M) − U(P) + U(O).
- **H1 (from the chat: positive in 40/40, mean +0.1825):** I > 0 in at least 30 of 40 worlds. Reported: mean, 95%
  bootstrap CI, count of positive worlds.
- **H2 ablation:** with cross-object exchange disabled, I = 0 in 40/40 (a sanity check of the harness, not a finding).
- **H3 (pierce ≠ attach):** U(move + pierce) ≠ U(move + attach) in at least 38 of 40 worlds; reported with which is
  higher, how often.
- **H4 (chat: one rotation changed a median of 46 connections vs 1 for an explicit wiring edit):** over 256 random
  overlapping configurations, the median number of links changed by one 90° rotation of B is greater than 1.
- **H5 codec:** encode each of 256 random worlds into a painting record (glyph label, colour, position, depth,
  properties) and decode it; execution identical in 256/256; relabelling all glyphs consistently leaves execution
  identical in 256/256. A check of the codec, not a discovery.

## R-004 (re-implementation of C1-EXP-004: multi-level visual programming)

- Scene left to right: grass, sky, car (surface + engine, seat, window inside at depth 1), road (+ white line).
  Program from T108: LINE grass.top → sky → triangle region at the car's centre (engine, seat, window) → road.white_line,
  after ENTER car DEPTH 1. Thermal environment seeded per world; utility at the sinks (`sinks_only`), measured as the
  change from the same scene with no program. 40 worlds.
- **H6 (chat: +0.1078 full triangle vs −0.0075 single point):** full triangle > single point in at least 30 of 40.
- **H7 (chat: whole car −0.0075):** selecting the car's internal modules > selecting the whole car in at least 30 of 40.
- **H8 (chat: reversed path −0.0175):** forward path > reversed path in at least 30 of 40.
- **H9 (chat: diverse-archive search beat random 12/12, +0.0399):** search over programs (4 points chosen from 12
  candidates incl. region shapes and sizes, direction), 12 seeds × 180 evaluations, selected on 3 training
  environments, scored on a held-out environment. Methods: random, basic evolution, diverse archive (MAP-Elites over
  number of modules selected × depth reached). H9: diverse archive > random in at least 9 of 12 seeds, bootstrap CI of
  the mean difference above 0.
