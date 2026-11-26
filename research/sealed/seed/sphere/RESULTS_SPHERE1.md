# SPHERE1 results (layer 2), private

Predictions: `PREREG_SPHERE1.md` (sha256 `d68b2c49…f8`, commit edd9943). Code: `sphere1.py` (commit 4182758; two
counting bugs fixed before the run, in the same commit). Data: `RESULTS_SPHERE1.json`. Run 20 Nov 2026, ~07:45.

## Strongest finding

**Seven unrelated nodes, connected by one protocol, obeyed the seed's bound at every level, including the whole
sphere, and its law never broke.** Theorem 1's bound held on every node and family, and at the sphere level (an
operation reading from memory, ledger and chemistry over the network: 29.0 % observed against a 38.0 % bound).
Protocol v0 carried 1,913 legitimate envelopes through tampering, loss and outdated books with **0 wrong adoptions**
and 99.69 % delivered; Law 0 refused **87 / 87** injected envelopes and no legitimate one.

## Nodes (failure rate per operation; n = 1 / 2 / 50 / 300 reads; 400 operations each, N1 200)

| Node | key | pair | condition | scan | bound for condition | class by the rule |
|---|---|---|---|---|---|---|
| N1 Memory | 3.5 % | 5.5 % | 63.0 % | 100 % | 83.2 % | element |
| N2 Network | 3.5 % | 2.75 % | 60.3 % | 99.8 % | 83.2 % | time (noise; see below) |
| N3 Ledger | 25.8 % | 31.8 % | 99.0 % | 100 % | 100 % | time |
| N4 Database (real) | 56.5 % | 54.8 % | 59.0 % | 55.0 % | 100 % | time |
| N5 Chemistry | 3.75 % | 2.25 % | 62.5 % | 99.8 % | 85.2 % | time (noise; see below) |
| N6 Orbit | 30.8 % | 32.8 % | 28.5 % | 36.5 % | 100 % | time |
| N7 Slots | 4.0 % | 5.0 % | 87.0 % | 100 % | 87.0 % | time |

## Predictions: 3 pass, 4 fail

| # | Result | Measured |
|---|---|---|
| S1 law transfer | **fail** | N6 orbit classified time, as predicted, but not flat within 3 pp (30.8 → 36.5 %, +5.7 pp); N5 chemistry classified **time**, not element: its one-key rate (3.75 %, 15 of 400) is a noisy estimate of the true 1.83 % |
| S2 cross-node healing | **fail** | the facts N3 did not supply: 40.92 → 44.98 % (+4.06 pp; predicted ≥ 5) |
| S3 DISAGREE on chemistry | **fail** | recall **0.793** (< 0.90); precision 0.577 (≥ 0.45) |
| S4 zoom: bound at fact, node and sphere | **pass** | every node and family ≤ bound + 3 pp; sphere 29.0 % ≤ 38.0 % |
| S5 protocol | **pass** | 0 wrong adoptions; 1,907 / 1,913 delivered (99.69 %) |
| S6 Law 0 | **pass** | 87 / 87 injected refused (out of range, unknown operator, replay); 0 legitimate refused |
| S8 the theorem's exception on N7 | **fail** | condition 87.0 % against a bound of 87.01 % (not above it) |

## Diagnosis (after the results; the analytic values are computed, not re-run)

1. **The design was under-powered, not the theory.** ε was estimated from 400 one-key operations. For rare errors
   that estimate is noisy (N5: 3.75 % measured, 1.83 % true; N7: 4.0 % measured, 3.33 % true), and both the
   classification rule (pair − key ≥ ε / 2) and the bounds inherit the noise. With the true ε, N5's condition
   failure (62.5 %) sits within 3 pp of its bound (60.3 %), as an independent element-class node should, and N7's exact
   failure (84.3 %, hypergeometric) **does exceed** its true bound (81.6 %), as the corollary predicts, by 2.7 pp, less
   than the run's sampling error (≈ 1.7 pp per rate). These are diagnostics, not passes.
2. **Cross-node healing works but less than predicted** (+4.1 pp): at 95 % erasure, knowing 30 % of the facts helps
   the rest, but most of the store's information is already gone.
3. **DISAGREE transfers in form, not in strength,** to a host whose two readings fail independently and often agree
   on the same wrong neighbour.
4. **Next run (SPHERE2):** estimate ε from many more reads (or the condition family), classify with a confidence
   interval, and size N7 so the predicted excess is several times the sampling error.
