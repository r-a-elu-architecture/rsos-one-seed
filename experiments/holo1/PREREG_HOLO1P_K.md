# HOLO1-P K: cascade with a state event (private, sealed 21 Nov 2026, 12:05 (UTC+02:00) Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius)

Why: owner 11:34 / U155: soup -> soap was a keyboard mistype (identity corruption), not an event. HOLO1-P P6 is
therefore invalid as a test of K. The sealed HOLO1-P files stay unchanged (D113); this is a separate seal.

System: the sealed `holo1p.py` (sha256 9828a280...57f1, checked at run time), S1 (leak 0.5, rho 0.95) and S2
(leak 0.15, rho 0.99), seed 1. Event at node 1 (kitchen), same objects, same identities:
A "the spoon is put on the table" vs B "the spoon falls on the floor". Chain kitchen -> computer -> company ->
family -> school, 40 trials, common random numbers.

Predictions (same pass rule as P6):
- **K1 (S2):** the event changes node 5's text in >= 25 % of 40 trials.
- **K2 (S1):** recorded; the HOLO1-P exploratory reading (memory N6 gates the cascade) predicts < 25 %.
- Recorded, not scored: change pattern per trial (gate at node 1 or not), amplifying and dampening nodes.
Note: the corpus contains neither "falls" nor "floor"; the event is new to the network, as an event is.
