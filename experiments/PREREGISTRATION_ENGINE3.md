# Pre-registration ENGINE3: guards grown from named causes, on real LLM agents

Written 20 Nov 2026, ~08:40 Vilnius, before any ENGINE3 model call. Harness: `experiments/a7_guard.py` (guards LATE,
DISAGREE, READY around the frozen B2 arm through `run_plan`'s planner hook; offline tests `test_a7_guard.py` pass).
Engine: `research/rsos_engine/`. Causes: AGENTS2 (errors grow along the plan, odds ratio 12.3), SC2 (stale values,
whole-state requests), FAILURES_MAP #51 (output cap).

## Design

- Model: Mistral Large 4 (owner's machine; key entered hidden). Set: SC1 (robot scene, 300 keys, 56 steps).
- **Calibration:** seeds 900–907. Candidates: {LATE, READY}, {DISAGREE, READY}, {LATE, DISAGREE, READY}; plus the
  unguarded B2. The engine (SCORE × TOTE) picks the candidate with the fewest wrong steps on calibration (ties: fewer
  calls).
- **Hold-out:** 16 SC1 seeds drawn from drand round **6660806** (21 Nov 2026, 10:00 UTC; chain of the earlier SC2
  draw): seed_i = first 8 bytes of sha256("<randomness>:ENGINE3:<i>"), i = 0…15. Run once: unguarded B2, the
  champion, and RSOS blind (X5b).

## Predictions

| # | Prediction |
|---|---|
| G1 | The champion guard halves JSON Patch's wrong steps on the hold-out (against unguarded B2) |
| G2 | It cuts last-quarter wrong steps by at least half |
| G3 | RSOS blind stays cheaper per correct task than the guarded JSON Patch agent |
| G4 | RSOS blind: 0 wrong steps on the hold-out |

Every prediction reported pass or fail; nothing changed after the run.
