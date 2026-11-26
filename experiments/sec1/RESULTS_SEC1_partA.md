# SEC1 results, part A (builds 1-2: supply, drift, protocol), 21 Nov 2026

Holm correction is applied across the hosts that measured each prediction (hosts 4-12 are not built yet).

| Prediction | supply (80 worlds) | drift (80 worlds) | protocol (48 worlds) | Verdict on measured hosts |
|---|---|---|---|---|
| P0 exact landing beats unhealed | 48/80, p 0.046 (Holm pass, m=2) | 80/80, p 8e-25 | whole vs unchecked 48/48, p 4e-15 | pass 3/3 |
| P1 spreads further with living structure | 77/80, p 7e-20 | 22/80 fail | not measurable | 1/2, fail |
| P2 exact beats global change of same size | 80/80 | 80/80 | bytes vs resend 48/48 | pass 3/3 |
| P3 gain grows with relation density | rho +0.17, p 0.12 fail | rho +0.15, p 0.17 fail | not measurable | fail 0/2 (sign now positive; HOLO3-6 were negative) |
| P4 whole message: 0 wrong and beats bare | not measurable | not measurable | 0 wrong of 9,600; bytes/correct 229 vs 1,938 bare, 48/48 | pass 1/1 |
| P5 beats the best native method | 48/80, p 0.046 (Holm pass, m=2) | 80/80, p 8e-25 | — | pass 2/2 |
| P6 induced operator transfers | not built | not built | not built | pending |

Disclosures: P1 in supply and P4 are partly by construction (no flow without channels; the hash check cannot adopt a
wrong book). Supply dose 0.6 set on smoke seed 999. P1 drift measure counts state differences 20 ticks after one heal
and came out near 0 in both arms (the heal is quickly overwritten by drift and use), so the drift host cannot show
spread with this measure.
