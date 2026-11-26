# PARTNERS5 short test: road 10 with K.11 + K.16 (24 Nov 2026, commit time exact; UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius)
Dev seed 6620; pairs v = 1, 4, 7, 10, 13, 16 (6 cells). Code `partners5.py` (c50475c, before the run).

## Result: PASSES all 7 checks — road 10 ready for the combined seal (n = 1, 2)
| Check | Result | Pass |
|---|---|---|
| R1 joined > best organism alone | 6/6 | yes |
| R2 joined > notubes | 6/6 | yes |
| R3 gain(2) > gain(1) = 0 | mean **+0.0183**, 6/6 positive (PARTNERS4 +0.0125) | yes |
| R4 every organism ≥ itself alone | **6/6** (PARTNERS4 36/40) | yes |
| R5 no landed joint action above a bound | **0** (PARTNERS4 2 ticks) | yes |
| R6 pool ≤ 4n | 0 ticks over | yes |
| R7 transferred landings with real need | 61/61 | yes |
Mean pair G: joined 0.9876 · notubes 0.9694 · aloneA 0.9514 · aloneB 0.9521 · native 0.9285.
Events: 1,174 particles freed, 62 transfers proposed, 61 landed, 1 refused by the membrane, 38 held by the rotation
(a donor not yet repaid), 0 refused by consent, joint gate never needed.
Reading: the rotation (rotating savings circle, reciprocal sharing, K.16) is the structure that closed R4; the joint
gate (admission control) closed R5. Short test: 6 cells; the seal decides the colour.
