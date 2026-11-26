# PREREG CONF5: the identified RSOS structure vs plain rollout, on fresh cells (25 Nov 2026)

Sealed (real/SEAL_CONF5.txt) and pushed before any CONF5 cell runs. Nothing is generated, tuned or re-run after the
seal (crashes only, disclosed). Later notes are dated addenda that change no rule. Layer: the layer-2 structure runs
unchanged on layer-1 data (a pass is cyan, LAYER_RULE).

## Question
Every earlier confirmation compared RSOS with the standard. Plain rollout (lookahead over the host's options, Bertsekas)
is the RSOS-free planning baseline, and STRUCT1 showed the bare structure only matches it. CONF5 asks: does the RSOS
structure that carries each row's gain beat plain rollout?

## How the structure was identified (landing rule, map Part I.5: read, match, bind, test on development cells)
PILOT1 (`real/pilot/PILOT1_NOTES.md`, development cells 1-8, never used here) ran the ladder standard / plain rollout /
seed v1 / full (v2 operators + persistent trace + composed programs):
- AI agents: only **full** beat rollout clearly (-27 % tokens, 7/8 cells, accuracy 0.97 vs 0.91); v1 alone 3/8.
- AI-AI: **v1** beat rollout (-27 % tokens, 6/8, accuracy 1.00 vs 0.875); full added nothing.
- Satellite: v1 too slow to screen locally; STRUCT1's sealed cells 301-308 (secondary reading): **v1** beat rollout 8/8, +0.74 %.
Disclosed: the pilot's 8 AI-agent jobs crashed once on an import order and were re-run after the fix.

## Design
- Arms per cell: `default` (the standard), `rollout` (plain rollout), and the row's identified structure:
  AI agents (self-consistency, gpt-oss-20b, cells 1001-1048): `full` = seed3 v2 (all 16 seed operators) + host levers +
  CONF3 composed programs, trace persistent over each job's 4 cells for this arm only;
  AI-AI (gpt-oss-20b + llama-3.1-8b, cells 1201-1300) and satellite (frozen CelesTrak elements, offline, cells
  1001-1020): `v1` = seed3v1 with the host's levers (Law 0 membrane, Law 4 landing, library P1-P8, native operator branches).
- Cell counts from the pilot's effect sizes (about 90 % power per row at the Holm threshold). 36 GitHub jobs.
- Note: plain rollout also uses the host's native branches, several of which the hosts map to RSOS operators (op_of);
  what rollout lacks is the seed (membrane, landing, library, futures valuation, operators, trace).

## Decision (fixed now; `real/analyze_conf5.py`)
A row passes if: (1) RSOS beats plain rollout, one-sided paired t, Holm over 3 rows, p < 1e-5 (tokens saved on the AI
rows, result on satellite); (2) guard on the AI rows: RSOS's result not worse than rollout's (mean >= 0 or 95 % lower
bound >= -2 %); (3) Law 0: no harm vs the standard (same guard).
**Levels:** UNPRECEDENTED = 3 of 3 rows · STRONG = 2 · NOT SHOWN = fewer. Reported only: AI-agent gain by position in job.

## Reproduction
`bash reproduce_conf5.sh` verifies every fingerprint and recomputes the table; `bash reproduce_conf5.sh space` re-runs
the satellite row offline (slow: 30-65 min per cell) and compares it with the committed run.
