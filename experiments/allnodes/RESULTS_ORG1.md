# ORG1 results: the violet organism (sealed 0728a7e; analysis analyze_org1.py exactly as PREREG_ORG1.md)

## Strongest finding
The injected structure S beat the best native method in all 21 shades, each significant after Holm over 21
(12/12 in 13 shades; holm p 0.005-0.022), and repeated on fresh seeds in every shade (>= 5/6 in both rounds).

## Five-measure rule per shade (U141)
m1 P0 and m3 P5: pass in 21/21. m5 repeat: pass in 21/21. m2 channels (>= 10/12 not worse): pass in 12/21
(v1, v2, v4, v6, v8, v9, v12, v13, v16, v19, v20, v21). m4 transfer (P14): FAIL at organism level (4/9 non-tied of 126;
117 ties). Under the sealed rule: 0 shades green.
Signal on m4 (build defect, not a law): the limited beam allowed 2 mode trials per landing, but 15 of 21 nodes have
at most 2 placements besides inside, so imprint-guided and random-guided beams tried the same modes -> ties. The
test had no power. Correction for ORG2: limit to 1 trial, so the imprint's choice matters.
Signal on m2: S occasionally trades the worst channel for the whole in 9 shades (7-9/12); the gate reads one future,
the measure reads the whole run.

## Organism-level predictions
| Prediction | Result | Level |
|---|---|---|
| P8b information: gain per flow, S > all-to-all | 242/252, p 3e-59 | exceptional |
| P4b protocol between 2 processes, corrupted messages | 0 corrupted adopted, 0 valid rejected; only 1 corrupted message in transit (10 % of 21) | pass, low power |
| P14 imprint transfer | 4/9 non-tied (126 runs) | fail (no power, see above) |
| P15 fever | no shade failed round 1 | not measurable |
| P16 birth on bridges | 11/37 | fail (reversed) |
| Real data P0r (U150) | 19/22, holm 0.001 | exceptional |
| Real data P5r (U150) | 11/24 (cancer 5/8, wine 6/8, digits 0/8) | fail |
| Real data P9r | 13/19, holm 0.17 | fail |

## Roadmap colour changes by the sealed rule
No row turns green. Grey rows whose layer-2 twin was built and run become yellow: Physics / physical layer (v6),
Physical comm layer (v4), AI chips (v10), Earth and space (v11), Level E (v14).
