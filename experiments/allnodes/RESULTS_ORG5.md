# ORG5 results (sealed b2a9689; analyze_org5.py exactly as PREREG_ORG5.md; full print ANALYSIS_OUT_ORG5.txt)

## Strongest findings
1. Structure crosses the bridge. Control (own structure > random of same size): 141/158, p 9e-26 - passes first.
   Transfer A (neighbour's structure, bound to the receiver, > random of same size): 141/176, p 1e-16 - PASS.
   First passing transfer in the series (ORG1-ORG4 all failed).
2. Real data (layer 1 data, cyan candidate): structure found on the OTHER two datasets beats the best native method
   (plain, decaying rate, hard-example mining) in 21/23 runs, p 3e-5, mean +8.8 accuracy points; own structure 20/24
   (p 8e-4). Control 15/21 (p 0.039) and transfer vs random 15/20 (p 0.021) pass.
   Structures: cancer own barrier+detect+memory; wine and digits own barrier+detect+adapt; each crosses to the others.
3. 11 shades pass every measure (provisional green): Network, Networks/satellites, Physical comm layer, Physics,
   Ledgers, Chemistry, Earth and space, Cosmology, Biology/medicine, Linguistics, Information theory.

## Against
- Claim B (neighbour's structure > best structure overall, no bridge): 4/72, p 1.0 - FAILS. The family shares one
  structure (detection + adaptive: 'd1a1g0b0' is the global best); bridges carry the family structure, not a
  neighbour-specific one.
- Channels (m2) fail in 10 shades: the clean guard is rarely chosen by the structures (it costs whole gain).
- m3 vs max(best native, beam-only) fails (Holm) in Level E, Law 1, Protocol theory, Level B, Operator algebra.
- Births by differentiation: 7/11, p 0.27 - FAIL.
- Critic note for real data: the barrier role is close to known noisy-label practice (small-loss / filtering);
  the hard data has 25 % label noise. ORG-FINAL must add such a baseline.

## Other
Worlds WB 18/21, WC 18/21 (p 7e-4 each). Gain per flow 245/252.
Colours: provisional (official only after ORG-FINAL on untouched seeds).
