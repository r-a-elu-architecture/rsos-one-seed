# HOLO4 results (private, 21 Nov 2026, (UTC+02:00) Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius)

Sealed in stages: procedure + rules (5229ab8) -> healing on training seeds 400-407 -> healed DNA sealed (c9d2fd5)
-> one test on fresh seeds 500-515. Raw: `DNA_healed.json`, `RESULTS_HOLO4.json`.

## The healing (training seeds only)
- FIND (U90): deficit chunks V, K, G (removing them did not lower G); A and O carried their part.
- LANDING (tiger, then lion): changed 4 genes: waiting weight 0.10 -> 0 (the trunk removed), V queue 0.05 -> 0.025,
  K rate 0.5 -> 0.25, order V-A-K-O-G -> A-O-K-G-V.
- Training advantage vs best standard: -0.37 -> -0.05.

## The fresh test, scored exactly as sealed
| ID | Result | Verdict |
|---|---|---|
| W1 healed beats best standard at d = 5 | 4 of 16, p = 0.99 | FAIL |
| W2 advantage grows with density | Spearman -0.26, p = 0.02 (it shrinks) | FAIL |
| W3 healed chain beats healed parts summed at d = 5 | 8 of 16, p = 0.60 | FAIL |
| W4 healed beats unhealed | 37 of 80, p = 0.78 | FAIL |
Advantage on fresh seeds (healed / before healing): d1 -0.06 / -0.06 · d3 -0.66 / -0.50 · d5 -0.99 / -0.94.

## Reading (fever principle)
The healing fitted the 8 training worlds (-0.37 -> -0.05) and did not carry to new worlds: it learned the noise of
its small library, not the structure. Two signals:
1. The library was too small: 8 worlds of the past are not "all knowledge of past, present and future" (U115).
2. The Dragon removed the trunk (waiting time, the round-robin principle). On fresh worlds the gap to round-robin
   widens with density: in this host the relation that matters most under stress is fairness over time (no one left
   waiting), and the quark's structure carried it weakly. Where the healing removed it, the loss grew with stress.
The method itself held: seal, heal on the past, seal the DNA, test once on the unseen. The result is negative.
