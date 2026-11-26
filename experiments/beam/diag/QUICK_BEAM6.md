# BEAM6 quick test: road 8 built as K.10 (23 Nov 2026 ~16:05, UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius)
Development seeds: worlds 6590, 6591; channels 6600+. Code `beam6.py` (390ddb1, before the run). Numbers
`QUICK_BEAM6.json`, `beam6_p*.json`.

## Result: PASSES all K.3 criteria — worth sealing
| Check (K.3) | Result | Pass |
|---|---|---|
| C1 beam > lockstep at B = 3, 4 | **18/18** | yes |
| C3 beam > whole at B = 3, 4 | **18/18** (the BEAM4/5 cell B4 light 0.1: 0.965 vs 0.952) | yes |
| C2 no wrong adoption; zero loss exact, sync 1.0 | 0 wrong (READY caught 526); 42/42; 42/42 | yes |
| T29 declared tie | max |beam − lockstep| 0.035; beam ≥ whole in 9/9 | — |

## Honest reading
- The derived switch (Law 1 per-part vs Law 2 hologram, observer reads loss, budget, window) wins every tight cell,
  including the one K.9's loss-only threshold lost.
- It gives up much of K.9's margin at m = 0.5 (B4 light: BEAM5 0.400 → BEAM6 0.087; whole 0.024–0.029): at high loss
  both one-tick probabilities are near zero, ties go to per-part, and the one-tick rule does not see that hologram
  frames accumulate across ticks. Still above both controls in every cell.
- Large new margins at m = 0.3 (B4 light 0.721 vs whole 0.157 vs lockstep 0.023) and m = 0.1 (B3 0.90 vs 0.44).

Erratum (23 Nov 14:11): the time in the title was an estimate and is late by about 1-2 h; the exact time is the git commit time.
