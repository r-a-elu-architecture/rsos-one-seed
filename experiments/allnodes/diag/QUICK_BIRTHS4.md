# BIRTHS4 short test: D with K.17 (book per state, gate by state) (24 Nov 2026, commit time exact; UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius)
Dev seeds 6690, 6691 (growth 6692, 6693); 7 bridges (14 cells). Code `births4.py` (dc95fc2, before the run).

| Check | BIRTHS3 | BIRTHS4 | Pass |
|---|---|---|---|
| B1 child > max(parents) in the child host | 0/14, mean −0.00001 | 2/14, mean −0.0001 | no |
| B2 child ≥ parent − 0.005 in the parent's own host | 25/28 | **26/28 (93 %)** | **yes** |
Mixed books (different parents for different states): 4/14 (BIRTHS3 2/14). Mean G in the child host: child 0.9559 ·
parent A 0.9383 · parent B 0.9548 (the child is above both parents on average, but not above the better parent of
each cell).
Data for step 1: the per-state book mostly still names one parent for every state (10/14); where it mixes, the child
gains little: in this host one parent's whole structure is usually better in every state, so routing between whole
structures cannot exceed the better one.
