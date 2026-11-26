# PILOT1 notes (25 Nov 2026, development cells 1-8 only; screening, never confirmation)

Ladder per row: default (standard) / rollout (plain rollout) / v1 (seed3v1 with the host's own levers) / full (seed3 v2 +
host levers + CONF3 composed programs + trace persistent over the arm's own 4 cells). Outputs: real/pilot/out/.
Runs: cloud 45669742702 (AI-AI ok; the 8 AI-agent jobs crashed on an import order in the pilot script), cloud
45670264303 (the 8 AI-agent jobs after the fix). Satellite: v1 and full were too slow to finish locally (sealed record:
seed3v1 takes 30-65 min per satellite cell); stopped; STRUCT1's sealed cells 301-308 used instead (secondary reading).

| Row | Rung that beats plain rollout | Effect vs rollout (8 cells) | Cells for p < 3.3e-6 at 90 % power (rough) |
|---|---|---|---|
| AI agents (self-consistency) | full (v2 operators + trace + composed) | -27 % tokens (10.3k vs 14.0k), 7/8 cells, accuracy 0.97 vs 0.91 | ~41 |
| AI agents | v1 | -17 % tokens, 3/8 cells | ~286 |
| AI-AI | v1 (membrane, landing, library, native operator branches) | -27 % tokens (1196 vs 1645), 6/8 cells, accuracy 1.00 vs 0.875 | ~94 |
| AI-AI | full | -22 %, 5/8; no gain over v1 | ~195 |
| Satellite (STRUCT1 cells 301-308) | v1 | +0.74 % result, 8/8 cells | ~19 |
