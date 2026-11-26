# HOUSE3 and LIVING2 short tests (K.17) (24 Nov 2026, commit time exact; UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius)
Code: house3.py, living2.py (dc95fc2, before the runs). Numbers: QUICK_HOUSE3.json, QUICK_LIVING2.json.

## HOUSE3 (Meaning; set-point rooms, vote in every room; seeds 6680, 6681; 14 cells): FAILS 0/4 → step 1
| Check | HOUSE2 | HOUSE3 |
|---|---|---|
| M1 house > best single object | 2/14, −0.0087 | 0/14, −0.0085 |
| M2 house > flat | 5/14, −0.0016 | 6/14, −0.0004 |
| M3 house > shuffled | 4/14, −0.0021 | 4/14, −0.0034 |
| M4 channels not worse | 9/14 | 5/14 |
Rooms now balanced (overload 314, uncertain 265, stable 261 of 840 ticks). Mean G: house 0.9099 · counter-shift alone
0.9149 · memory 0.9124 · apoptosis 0.9120 · vote 0.9117 · flat 0.9103 · shuffled 0.9133 · native 0.8649.
Data: with the rooms balanced the house is still below each single object: switching objects between ticks costs more
than any object gains in its room; the best single object differs by cell (the oracle "best single" is the max of five).

## LIVING2 (E; observer reads adaptation, re-targets; seeds 6700, 6701; 14 cells): FAILS E1 (12/14) → step 1
| Check | LIVING1 | LIVING2 |
|---|---|---|
| E1 structure > best native in every cell | 13/14 (+0.019) | 12/14 (+0.025) |
| E2 observer vs v3 | identical (never fired) | 5 wins / 9 losses, mean −0.0019; 37 re-targets per run |
Data: the observer now acts, but moving landings off adapted units costs more than it saves; v3 alone stays above
every native in most cells of the living host.
