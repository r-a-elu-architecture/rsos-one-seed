# ORG2 results (sealed 3f792cd; analyze_org2.py exactly as PREREG_ORG2.md)

## Strongest finding
Temporal placement on real data (P5t): the structure now beats the best native method, decaying rate included:
19/23, p 0.0013 (vs decaying rate alone 20/24, p 0.0008); wine 8/8, cancer 6/7, digits 5/8 (ORG1: 0/8).
And again S beat the best native in all 21 shades (12/12 in 20 shades, 11/12 in one), Holm p 0.005 each.

## Per shade (five measures)
m1, m3, m5: 21/21. m2 channels >= 10/12: 11/21 (v2, v3, v6, v8, v11, v12, v13, v16, v17, v20, v21).
m4 transfer P14': 6/9 non-tied of 126 (p 0.25): FAIL. 0 shades green under the sealed rule.
Signal on m4 (design defect, deeper than in ORG1): 17 of the 24 nodes have exactly ONE placement besides inside and
2 have none, so an imprint about which placement to use cannot differ from a random choice there; 117/126 runs tie
by construction. Transfer of placement choice is untestable in these nodes; transfer has to carry something that
can differ (where, when, how much).
Signal on m2: the channel measure moved between runs (Law 2 10 -> 7, Databases 10 -> 5, Networks/satellites 9 -> 12):
S trades the worst channel for the whole in part of the runs; the gate reads the default future, not the realised one.

## Organism level
| Prediction | Result |
|---|---|
| P5t real data, temporal placement | 19/23, p 0.0013: PASS (exceptional) |
| P8b information, gain per flow | 252/252, p 1e-76: PASS (unprecedented in this series) |
| P14' transfer | 6/9 of 126: FAIL (no power) |
| P16' births by vary + select | 8/25: FAIL |
| P4b' protocol | 0 of 5 corrupted adopted, 0 valid rejected; only 5 corrupted (rule needs >= 8): not measurable |
| P15 fever | no shade failed round 1: not measurable |

## Colours by the sealed rule
No row turns green. Biology/medicine, ML on real data and Level C gain the real-data pass they were missing (P5t).
