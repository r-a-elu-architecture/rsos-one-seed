# QUICK_ORGANS1: short tests of Meaning, D, E on the K.18 organ host (development, no colour)
Code: organs.py (commit 6903bcf, checks fixed before the run). Seeds 6720/6721, shades 1,4,7,10,13,16,19.

| Row | Check | Result | Pass |
|---|---|---|---|
| Meaning (house4) | M1 house > best single per cell | 8/14, mean −0.0014 | no |
| | M2 house > flat | 12/14, mean +0.0229 | yes |
| | M3 house > shuffled | 8/14, mean +0.0026 | no |
| | M4 channels ≤ best single | 6/14 | no |
| D (births5) | B1 child > max(parents) | 0/8, mean −0.0265 | no |
| | B2 child ≥ own parent − 0.005 | 8/16 | no |
| E (living3) | E1 observer > best native | 3/14, margin −0.0147 | no |
| | E2 observer vs v3 | 0 wins / 14 losses, mean −0.046 | (reported) |

Mean G (house test): house 0.8815 · liver room 0.8800 · shuffled 0.8789 · kidney 0.8721 · lungs 0.8709 · flat 0.8586 · heart 0.8584 · native 0.8273.
Births: the run stopped after 8 of 14 cells (the environment ended the processes); B1 at 0/8 cannot reach 2/3 of 14, so the verdict holds.
Rule 0.1: every row failed, so all three go back to step 1 (identification). No rebuild by trial.
