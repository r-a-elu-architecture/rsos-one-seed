# OPS2 results (layer 2), private

Predictions: `PREREG_OPS2.md` (sha256 `98bde57f…f1e`, commit a103a09). Code: `ops2.py` (commit af6bfb0, before any
result). Data: `RESULTS_OPS2.json`. Run 20 Nov 2026, ~06:10 Vilnius.

## Strongest finding

**On a real database engine, Law 1's ordering disappears and its upper bound survives.** SQLite fails about one
operation in three whatever the operation reads (33.5 % for one row, 32.2 % for 20, 36.9 % for 300), because its
failures are set by time (the writer's lock), not by element: an operation either meets the lock at its start or
finishes before the next one. Blind operation gains nothing there. So the universal part of Law 1 is the bound, not
the ordering:

**Law 1′, held on all five hosts so far:** P(fail) ≤ 1 − (1 − ε)^n. It is reached when errors are independent per
element (memory), lies below it when errors cluster (network, ledger, LLM agents), and collapses to ε when errors are
set by a time window shorter-lived than the operation (SQLite).

## Results

| # | Result | Measured |
|---|---|---|
| R1a LLM agents: Law 1 as an upper bound (retrospective) | **pass** | pair 0.168 % ≤ 0.281 %; scan 2.31 % ≤ 2.63 % (n = 19, the tightest bound; 15.7 % at the mean state size) |
| R1b LLM agents, SC2 out of sample | **pass** | derive_where 14.84 % ≤ 34.38 % (n = 300) |
| S1 SQLite pull ordering | **fail** | 33.5 / 34.5 / 31.7 / 32.2 / 36.9 % for 1 / 2 / 5 / 20 / 300 rows: flat |
| S2 SQLite Law 1 as an upper bound | **pass** | every pull rate ≤ the bound (55.8 / 87.0 / 99.97 % for 2 / 5 / 20) |
| S3 SQLite blind ≤ 2 ε, pull(20) ≥ 5 ε | **fail** | blind is as flat as pull (26.3–33.4 %); pull(20) 32.2 % < 5 × 33.5 % |
| S4 Law 0: no partial result served | **pass** | 0 |

**4 pass, 2 fail.** ε on SQLite came out at 33.5 % in this run (calibration had shown 0.36–17 %); predictions use
the ε of the run itself, as sealed.

## Diagnosis

1. The seed's law needs one host property it did not have: **what an error belongs to.** Per element (memory,
   network packets, LLM reads): failure grows with read scope, and blind operation pays. Per time window (a lock):
   scope does not matter, and the remedy is timing (retry, waiting), not blindness.
2. Next form to test (sealed first): n_eff = the number of independent error events an operation spans; P(fail) ≈ 1
   − (1 − ε)^n_eff, with n_eff from element count and the host's correlation time. Predicted: SQLite's ordering
   returns when operations last longer than the writer's cycle.
3. R1 is retrospective on data whose ordering was already known; only its quantitative bound and R1b were new.
