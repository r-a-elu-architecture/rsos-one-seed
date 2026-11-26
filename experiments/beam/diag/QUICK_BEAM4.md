# BEAM4 quick test: road 8 built as K.7 (23 Nov 2026 ~14:25, UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius)
Development seeds: worlds 6540, 6541; channels 6550+. Code `beam4.py` (5f816fe, before the run; one implementation fix
from a throwaway smoke test, recorded in the docstring). Numbers `QUICK_BEAM4.json`, `beam4_p0.json`, `beam4_p1.json`.

## Result: FAILS on C3 (2 of 3 criteria pass) → back to step 1 (rule 0.1), no rebuild
| Check (K.3) | Result | Pass |
|---|---|---|
| C1 beam > lockstep at B = 3, 4, every cell | **18/18** | yes |
| C2 no wrong adoption; zero loss exact, sync 1.0 | 0 wrong (READY caught 454); 42/42 exact; 42/42 sync 1.0 | yes |
| C3 P3 carrier (beam) > whole resend at B = 3, 4 | **11/18**: loses all 6 cells at m = 0.5 and B4 light 0.1 (0.925 vs 0.936) | **no** |
| T29 (declared tie, reported) | beam vs lockstep up to 0.091 apart (beam ahead at m = 0.5); whole ahead of both at m = 0.5 (radio 0.933 vs 0.803) | — |

## Data for the next identification (no diagnosis-by-rebuild)
- The flowing carrier with green-dot feedback raised the beam strongly against BEAM3 at B = 29 (light 0.3: 0.977 vs
  0.688; radio 0.5: 0.803 vs 0.485) and at tight budgets with low loss (B4 light 0.1: 0.925 vs 0.825).
- Where it loses (high loss, backlog): each part travels in its own envelope (16-bit check + 4-byte READY, at least
  one whole frame), while the whole bundle shares one READY across the backlog and decodes from any k frames of the
  bundle; and when an acknowledgement is lost the carrier spends frames on parts the receiver already holds.

Erratum (23 Nov 14:11): the time in the title was an estimate and is late by about 1-2 h; the exact time is the git commit time.
