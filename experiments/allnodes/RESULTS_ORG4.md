# ORG4 results (sealed 47d5b52; analyze_org4.py exactly as PREREG_ORG4.md; full print in ANALYSIS_OUT_ORG4.txt)

## Strongest finding
The structure wins in two structurally different worlds: bursts WB 42/42 (p 2e-13), cascade WC 38/42 (p 3e-8).
"One world with 21 settings" no longer holds as an objection to S beating the natives.

## Transfer (m4): FAIL, and the control says why
Library-guided vs random 12 landings: 59/125 (p 0.76). Own-shade library control: 39/72 (p 0.28): even a shade's
OWN past does not pick better landing times than chance. Landing precision: library 18 %, random 24 %.
Diagnosis: in these twin worlds the value of one landing tick is near zero almost everywhere (80th percentile
~1e-4) and is not predictable from the situation; WHEN to land is not a learnable quantity here, so no lesson about
it can transfer. This closes the timing-transfer line in the twins (as stated before the run).

## Stronger baseline (critic point 4)
Beam-only (default picks + full placement search) beats the best native 189/214 (p 1e-32): much of S's margin
comes from the placement search itself. S vs max(best native, beam-only): Holm < 0.05 in 5 shades (v3, v4, v5,
v15, v17); 11/12 (Holm 0.051) in 7 more; Linguistics 5/11, Information theory 3/11, Operator algebra 6/12, Biology 7/12.

## Clean guard (critic point 1)
Without any native information: channels >= 10/12 in 13/21 shades (ORG3 with native-reading guard: 21/21).
Guard used on 24 of 60 ticks on average.

## Kept
Protocol: 9 corrupted, 9 rejected, 0 adopted, 0 valid rejected: PASS. Gain per flow 247/252: PASS.
m1 vs plain native: 21/21 shades at 10-12/12.

## Colours
0 greens (provisional rule): unchanged 19 green / 31 yellow / 1 grey.
