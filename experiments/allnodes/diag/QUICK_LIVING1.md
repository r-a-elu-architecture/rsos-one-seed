# LIVING1 short test: row E with K.14 + K.16 (24 Nov 2026, commit time exact; UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius)
Dev seeds 6660, 6661; shades 1, 4, 7, 10, 13, 16, 19 (14 cells); living twin (tolerance + resistance). Code `living1.py` (59b5eea).

## Result: FAILS E1 by one cell (13/14) → back to step 1
| Check | Result | Pass |
|---|---|---|
| E1 structure > best native in every cell while the host adapts | 13/14, mean margin +0.019; the one loss: shade 16, seed 6661, 0.9933 vs beam-only 0.9942 | no |
| E2 (reported) observer vs v3 | identical in 14/14: the explore trigger never fired (explore share 0.000) | — |

## Data for step 1
- The structure keeps its margin in the living host in 13/14 without any observer: v3 alone is above every native there.
- The observer of the observer, as built, never acted: its error (predicted vs observed dry and drifted counts, one
  tick ahead) never exceeded 1.5 x its running mean; the explore trigger is not reading the host's adaptation.
- The one loss is at the ceiling (0.993 vs 0.994) against beam-only, in a shade whose own structure is shallow.
