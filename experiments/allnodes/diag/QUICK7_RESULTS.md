# Quick loops 22 Nov 18:55–19:35 (development seeds 7000–7001 = DIAG1 seeds; no colours)

Organism v2 roles (org7.py) on top of each shade's ORG6 structure; gap = G − bar (strongest native or beam-only);
channels = no channel worse than the native.

| Role | Shades | Runs | gap > 0 | channels ok | both |
|---|---|---|---|---|---|
| none (ORG6 as is) | 14 non-green | 28 | 20 | 22 | 15 |
| **cs** (P1 counter-shift, threshold 2) | **all 21** | 42 | **41** | **42** | **41** (one tie: v21, 0.0000) |
| cs1 (threshold 1) | 17 | 34 | 34 | 33 | 33 |
| cs + mem | 14 | 28 | 28 | 28 | 28 |
| vote (P8) | 14 | 28 | 20 | 22 | 14 |
| mem (P5/P6) | 14 | 28 | 20 | 23 | 17 |
| joint (P4) | 14 | 28 | 20 | 21 | 14 |

Reading: one primitive, counter-shift (the unit that sets a channel pulls a landing to itself), closes the channel
failures and adds margin on every shade; vote, memory and joint choice alone change little. Margins stay thin on
v18 (+0.0004), v19 (+0.0008), v21 (0.0000), v14, v15, v17 (+0.003) on the second seed. Chosen for the sealed run:
**cs, threshold 2**, the only variant checked on all 21 shades, as one universal rule.
