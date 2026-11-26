# Pre-registration ORG7: organism v2 with counter-shift (22 Nov 2026 ~19:40 Kyiv), sealed in SEAL_ORG7.txt before any ORG7 seed

## Build (owner's method: structure first, quick test, then one long run)
DIAG1 found 14 non-green shades failing on thin margins over beam-only and on channel 1. Part I of the structural map
gave the primitives; the quick loops (diag/QUICK7_RESULTS.md, development seeds only) selected **P1 counter-shift**:
the unit that sets a channel (longest dry supply unit, longest drifted unit) pulls one landing to itself when its run
reaches 2 ticks. Organism v2 = ORG6's structures (picked on ORG6's selection seeds, untouched) + counter-shift for
every arm (own, nb, glob, random structures, worlds). One universal rule; no per-shade choice.

## Unchanged
run_st (org5.py), ORG6 picks (org6.py, org6/sel_*.json), arms, natives, beam-only, worlds WB / WC, the five measures
and Holm (analyze_org7.py = analyze_org6.py with file names changed).

## Seeds (fresh): evaluation 9490–9501 (12); worlds 9960; random structures 9890+.

## Predictions (fixed now)
- **R1:** channels (m2 ≥ 10/12) pass in at least 19 of 21 shades.
- **R2:** at least 15 of 21 shades green (all measures).
- **R3:** all 21 green (the owner's target; the thin margins on v14, v15, v17, v18, v19, v21 make it uncertain).
- **R4:** control and transfer (m4) and worlds (m6) pass.

## Colours
A shade green under ORG7 turns its row green (turquoise, layer 2). Rows green from FINAL or ORG6 that fail here are
reported next to their colour. The centre rows (Mathematics, Distributed systems) turn green only if all 21 are green
under this one rule.

## Run (owner's laptop, 4 parts in parallel, ~40–60 min)
python org7run.py 0 ; python org7run.py 1 ; python org7run.py 2 ; python org7run.py 3   (four PowerShell windows)
python analyze_org7.py > ANALYSIS_OUT_ORG7.txt
