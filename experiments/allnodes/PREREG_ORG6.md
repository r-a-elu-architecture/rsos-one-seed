# Pre-registration ORG6: heal without harm (22 Nov 2026 ~14:30 Kyiv), sealed in SEAL_ORG6.txt before any ORG6 seed runs

## Why (from ORG-FINAL, ANALYSIS_OUT_FINAL.txt)
16 of 21 shades are not green. 7 fail **only m2** (channels: own worst channels not worse than the native in ≥ 10/12):
v1 (8/12), v4 (9), v5 (7), v7 (9), v9 (8), v10 (7), v17 (8). Six of these seven chose a structure with the guard **off**:
selection maximised the whole G and was blind to the host's channels. The other 9 fail m3 (beating the strongest baseline)
and/or m5; ORG6 does not address them and predicts no change there.

## The one change
Selection follows Law 0 ("do no harm"): a structure is admissible for a shade only if, on both selection seeds, none of
its channels is worse than the native's (all roles off = report+popular exactly). Own = best admissible by mean G; nb =
best admissible on both neighbours; glob = best admissible on all other shades. The native is always admissible.
Everything else is ORG5/FINAL unchanged: run_st (org5.py, hash-checked), arms, natives, beam-only, worlds WB/WC, the five
measures and Holm (analyze_org6.py = analyze_final.py with file names changed; births and real data not run).

## Seeds (fresh, never used): selection 9460–9461; evaluation 9470–9481 (12); worlds 9950; random structures 9880+.

## Predictions (fixed now)
- **Q1:** m2 passes (≥ 10/12) in at least 5 of the 7 m2-only shades {v1, v4, v5, v7, v9, v10, v17}.
- **Q2:** at least 4 of those 7 shades pass all measures (turn green under this rule).
- **Q3 (risk stated):** the admissible structure may have lower G; m1 and m3 may then fail in some of the 7. Reported per shade.
- **Q4:** the 9 m3/m5 shades: no prediction of improvement.
- **Q5:** control and transfer (m4) still pass globally (p < 0.05).

## Colours
A shade that passes all measures in ORG6 turns green for its row under the ORG6 rule (turquoise, layer 2). FINAL's five
greens keep their colour from FINAL; if any of them fails in ORG6 it is reported next to its colour, not hidden.
Centre rows still need all 21 shades green under one rule.

## Run
python org6.py select 0 & python org6.py select 1 ; then python org6.py eval 0 & python org6.py eval 1 ;
python analyze_org6.py > ANALYSIS_OUT_ORG6.txt
