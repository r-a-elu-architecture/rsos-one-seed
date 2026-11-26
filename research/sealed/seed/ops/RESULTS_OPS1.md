# OPS1 results (layer 2), private

Predictions: `PREREG_OPS1.md` (sha256 `c55a9b2b…013f`, commit d851821, before any code). Code: `ops1.py` (commit
5a3b8c5, before any result). Data: `RESULTS_OPS1_part1.json`, `RESULTS_OPS1_part2.json`. Run 20 Nov 2026, ~05:40–05:50
Vilnius; code unchanged during the run.

## Strongest finding

**The same seed laws hold on three hosts that share nothing.** On a holographic memory, a packet network with burst
loss and a replicated ledger with rack failures, failure grows with what an operation must read (Law 1), in the same
order on all three. Blind operation (Law 2) makes failure flat: on the network 4.0–4.5 % for every read scope against
2.4 % → 99.2 % when values are pulled; on the ledger 24–26 % flat against 26 % → 100 %. Under all of it, the Law 0
monitor refused **2,276 of 2,276** injected violations before they took effect and **0 of 22,013** legitimate actions.

## Part 1: operators

| # | Result | Measured |
|---|---|---|
| Z1 violations refused before effect | **pass** | 2,276 / 2,276 (O1 618, O2 1,600, O3 26, O4 32); SEE and LOOP had no injected violations (not tested there) |
| Z2 no legitimate action refused | **pass** | 0 / 22,013 |
| O1 CARRY + READY | **pass** | 0 wrong adoptions; 99.85 % of legitimate messages delivered (1,956 / 1,959); 41 out-of-range messages never delivered |
| O2 LAND | **fail** | precision 1.000 (≥ 0.90), facts after 99.98 % ≥ before 99.94 %; recall **0.316** (< 0.40) |
| O3 ISOLATE | **fail** | located 150 / 150; 0 reads served from an isolated part; checks for k = 1: **25** against a bound of 24 (the root check was not counted in the bound); k = 4: 87 ≤ 96; k = 16: 279 ≤ 384 |
| O4 GROW | **pass** | 96.65 % against plain 93.13 % (+3.5 pp); budget never exceeded |
| O5 SEE | **fail** | seer 2 flags 99.7 % of seer 1's errors; precision **0.134** (< 0.20); the witness stops (≤ 3 passes) and lifts 93.13 % → **99.96 %** |
| O6 LOOP | **pass** | see: thresholds 0.5 / 0.7 / 0.9; build: 0.9; decide: accepted. Held-out at 70 %: **99.21 %** (gate 0.5: 96.67 %); at 90 % unchanged (54.58 %) |

## Part 2: Law 1 and Law 2 on three hosts (failure rate per operation)

| Host | | key (1) | pair (2) | condition (50) | scan (300) |
|---|---|---|---|---|---|
| Memory | observed | 1.75 % | 4.69 % | 58.66 % | 99.88 % |
| | Law 1 predicted | | 3.47 % | 58.64 % | 99.50 % |
| Network | observed (pull) | 2.38 % | 3.97 % | 57.00 % | 99.16 % |
| | Law 1 predicted | | 4.69 % | 69.94 % | 99.93 % |
| | blind | 4.03 % | 4.28 % | 4.06 % | 4.53 % |
| Ledger | observed (pull) | 25.97 % | 31.56 % | 99.38 % | 100 % |
| | Law 1 predicted | | 45.19 % | 100 % | 100 % |
| | blind | 26.28 % | 23.91 % | 24.28 % | 25.19 % |

| # | Result | Measured |
|---|---|---|
| L1a ordering on all three hosts | **pass** | key < pair < condition < scan everywhere |
| L1b memory within max(3 pp, 30 %) | **pass** | pair 4.69 vs 3.47; condition 58.66 vs 58.64 |
| L1c correlated hosts below Law 1 | **pass** | network 57.00 < 69.94; ledger 99.38 < 100 |
| L2a blind flat, pulled ≥ 10× | **fail** (as one row) | blind scan ≤ 2 × key: network 4.53 ≤ 4.75, ledger 25.19 ≤ 51.94 (pass); pulled scan ≥ 10 × key: network 99.16 ≥ 23.75 (pass), ledger **impossible as written** (10 × 25.97 % exceeds 100 %; a sealing error) |

**Totals: 8 pass, 4 fail.**

## Diagnosis (after the results)

1. **Law 1 is quantitative on the independent host** (condition 58.66 vs 58.64 predicted) and an upper bound on the
   correlated ones: bursts cluster failures, so fewer operations fail than compounding predicts.
2. **Law 2 has a price at small scope:** blind costs two messages, so for one key it is worse than pulling (network
   4.03 vs 2.38 %). It pays from two keys up and is decisive at scale.
3. **LAND is exact but cautious** (precision 1.000, recall 0.316): the margin rule lands only where the need is
   certain. A lower margin trades precision for recall; not tuned after the run.
4. **SEE's second seer over-flags** (precision 0.134) but misses almost nothing (99.7 %); the witness turns that into
   99.96 %. The seer of seers works as a net, not as a judge.
5. **LOOP fixed the T2c gate** without touching the test scenes: 96.67 → 99.21 % at 70 %.
6. Prior art: compounding failure and moving computation to data are established. What is new here is one seed, the
   same operators and laws, and one Law 0 monitor across unrelated hosts, sealed before each run. Hosts are
   simulations (layer 2); three hosts, not six.
