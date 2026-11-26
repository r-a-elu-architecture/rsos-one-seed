# PARTNERS4 quick test: road 10 built as K.6 (shared pool 4n) (23 Nov 2026, commit time is exact; UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius)
Dev seeds 6560, 6561; 20 bridge pairs x 2 = 40 cells (n = 2; n = 1 gain 0 by definition). Code `partners4.py`
(7a96cdd before the run; resume added d195226, execution only). Numbers `QUICK_PARTNERS4.json`, `partners4_p*.json`.

## Result: FAILS on R4 and R5 (5 of 7) → back to step 1 (rule 0.1), no rebuild
| Check | Result | Pass |
|---|---|---|
| R1 joined > best organism alone | **40/40** | yes |
| R2 joined > notubes | **38/40** | yes |
| R3 gain(2) > gain(1) = 0 | mean **+0.0125** (PARTNERS3 +0.0011, PARTNERS1 −0.0008); positive in 38/40 | yes |
| R4 each organism ≥ itself alone (no tolerance) | **36/40**; the 4 losses: −0.0004 … −0.0013 in one world | **no** |
| R5 no landed joint action above a world's bound | **2 ticks**, both in one cell (pair 6, seed 6560) | **no** |
| R6 pool conserved (≤ 4n) | 0 ticks over | yes |
| R7 transferred landings with measured need | **0.996** (453/455) | yes |
Mean pair G: joined 0.9855 · notubes 0.9729 · aloneA 0.9592 · aloneB 0.9548 · native 0.9381.
Joined events: 9,174 particles freed (no need), 508 transfers proposed, 53 refused by the per-world membrane, 93
would have harmed a receiver, 455 landed.

## Data for the next identification
- **The shared pool is the structure the tube was missing:** with the same total resource (4n), coordination raises
  the pair by +0.0125 over two independent organisms (11x the PARTNERS3 gain), in 38/40 cells.
- R4: in 3 of the 4 losing cells the losing world ended the run as a net giver of 3 particles (debt 3): repayment
  was preferred, not guaranteed, and the run ended before it came back; one losing cell had debt 0.
- R5: 2 ticks in one cell landed above a world's bound: the final per-world guard's fallback checks each organism's
  action with the partner on defaults, not the two actions jointly.
