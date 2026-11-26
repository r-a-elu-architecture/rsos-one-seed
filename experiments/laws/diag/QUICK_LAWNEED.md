# LAWNEED: cheaper Law 4 need vs the full own-future fork (23 Nov 2026 ~12:50, UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius)
Development seed 6530; shades 3, 10, 17; decision ticks 5, 15, 25, 35 (tick 45 was never reached: the driving loop
stops at t < 45, a defect; 12 decision points, 48 landings). Code `lawneed.py` (c1a60a7, before the run).
Reference FULL_CRN = own-policy futures with common randomness (decisions do not change the world's events).

| Method | Agreement with reference | Wrongly withheld | Wrongly kept | s per tick (here) |
|---|---|---|---|---|
| FULL (as LAWS4 runs it) | **0.604** | **0.229** | 0.167 | 13.1 |
| OPEN (candidate: replay the recorded plan) | 0.792 | **0.000** | 0.208 | **2.5** |
| H5 (own policy 5 ticks, then defaults) | 0.688 | 0.167 | 0.146 | 2.8 |
Reference need rate 0.354; reference cost 13.0 s per tick. Candidate check (≥ 95 % agreement, ≤ 2 % wrongly
withheld): **fails** on agreement (0.792), passes on wrongly withheld (0.000).

## Findings
1. **LAWS4's own need measure is mostly noise.** Without common randomness, the futures with and without a landing
   meet different world events (the organism's decisions draw from the world's generator a branch-dependent number of
   times). FULL agrees with the noise-free reference on 60 % of landings and would withhold 23 % of landings the
   reference says are needed. LAWS4 (running on the laptop, results unread) measures Law 4 this way.
2. **OPEN never withholds a needed landing** (0 of 48) and costs 5x less, but keeps 21 % of landings the reference
   says are not needed (open-loop replay cannot re-decide after a removal, so removals look more harmful than they
   are): conservative, not exact.
3. The same generator coupling made the Law 0 gate fire against its own bound in LAWS3/LAWS4 projections (seen in the
   PARTNERS3 smoke test and fixed there by common randomness).
