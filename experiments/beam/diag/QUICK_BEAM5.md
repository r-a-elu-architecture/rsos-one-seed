# BEAM5 quick test: road 8 built as K.9 (23 Nov 2026 ~15:20, UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius)
Development seeds: worlds 6570, 6571; channels 6580+. Code `beam5.py` (0c25a1a, before the run). Numbers
`QUICK_BEAM5.json`, `beam5_p*.json`.

## Result: FAILS by one cell on C3 (17/18) → back to step 1 (rule 0.1), no rebuild
| Check (K.3) | Result | Pass |
|---|---|---|
| C1 beam > lockstep at B = 3, 4 | **18/18** | yes |
| C2 no wrong adoption; zero loss exact, sync 1.0 | 0 wrong (READY caught 478); 42/42; 42/42 | yes |
| C3 beam > whole at B = 3, 4 | **17/18**; the one loss: B4 light 0.1, 0.9317 vs 0.9488 | **no** |
| T29 declared tie | max |beam − lockstep| 0.033; beam ≥ whole in 6/9 B29 cells | — |

Mean sync, beam / lockstep / whole, at m = 0.5: B3 light 0.165 / 0.003 / 0.016; B4 light 0.400 / 0.009 / 0.029;
B4 matter 0.373 / 0.010 / 0.043; B4 radio 0.293 / 0.016 / 0.037 (BEAM4 per-part only: 0.022 / 0.029 / 0.029).
Hologram share of ticks (beam): m = 0.1: 0.002–0.016; m = 0.3: 0.11–0.28; m = 0.5: 0.65–0.84.

## Data for the next identification
- The route by state works where K.9 placed it: at m = 0.5 the hologram of the backlog lifts the beam 5–14x over
  the whole-resend control and 13–50x over lockstep.
- The one losing cell (B4 light 0.1) is in per-part mode (hologram share 0.009); BEAM4 lost the same cell
  (0.925 vs 0.936). At low loss with B = 4 the whole bundle (one READY) wins narrowly against per-part envelopes.

Erratum (23 Nov 14:11): the time in the title was an estimate and is late by about 1-2 h; the exact time is the git commit time.
