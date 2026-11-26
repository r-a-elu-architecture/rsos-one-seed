# BIRTHS3 short test: row D with K.13 + K.16 (24 Nov 2026, commit time exact; UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius)
Dev seeds 6650, 6651 (growth 6652); bridges 1, 4, 7, 10, 13, 16, 19 (14 cells). Code `births3.py` (55c0759).

## Result: FAILS (B1 0/14, B2 25/28) → back to step 1
| Check | Result | Pass |
|---|---|---|
| B1 child > max(parents) in the child host | 0/14 wins, mean −0.00001 (ties with the stronger parent) | no |
| B2 child ≥ parent − 0.005 in the parent's own host | 25/28 (89 %) | no |
Mean G in the child host: child 0.9711 · parent A 0.9560 · parent B 0.9710.

## Data for step 1
- The book named the SAME parent strong on both channels in 12 of 14 cells (dominance, not complementation): the child
  then is that parent, so it ties it. Strength read per channel over the whole run cannot separate the parents.
- Where the book was mixed (bridge 10), the child tied both parents.
- B2: the child loses up to 0.02 in parent A's own host when the book picked parent B (the child carries B's structure
  into A's host).
