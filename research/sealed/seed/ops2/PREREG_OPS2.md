# OPS2: the seed's laws on real hosts: real LLM agents (retrospective) and a real database engine (new)

Written 20 Nov 2026, ~06:05 Vilnius. Private. Follows OPS1 (simulated hosts). No OPS2 analysis code exists when this
file is committed.

## R1: real LLM agents (retrospective, labelled as such)

Data: the 19 A7/A8 result files in RSOS-Language `results/a7_results_*.jsonl` (real runs of Opus, Sonnet, Haiku,
GPT, Gemini, Mistral, gpt-oss; SC sets excluded), already summarised by operation kind in `OPERATION_TABLE.md` §3
(19 Nov). The ordering is therefore **known**; what was never computed is the quantitative form of Law 1. State size
per run: 19–304 keys (mean 121.7), measured from `final_state` before this file.

- **R1a (Law 1 as an upper bound).** With ε = one-key failure of JSON Patch (10 / 7,125), observed failure for two
  keys and for the whole-state scan is at or below 1 − (1 − ε)^n, using n = 2 and, for the scan, the **smallest**
  state size (n = 19, the most conservative bound).
- **R1b (out of sample, sealed earlier).** SC2 (pre-registered 19 Nov, drand-drawn, Mistral): JSON Patch failure on
  derive_where requests ≤ 1 − (1 − ε)^300 (the SC2 state size).
- Law 2 on this host is reported, not predicted: RSOS blind steps failed 0 in every row (known).

## R2: a real database engine (new, unseen)

Host: SQLite 3.53.1 (real engine, real file locks, real OS scheduling), table of 300 rows (one per fact), rollback
journal. One writer process commits single-row updates continuously (pause 10 ms, synchronous off). A reader with
busy timeout 0 performs operations; a read fails when the engine reports the database locked.

Calibration (disclosed, before this file; `calibration_sqlite.py`): with this setting the one-key failure varied
between runs from 0.36 % to 17 %. So families are **interleaved at random within one run**, and ε is measured in that
run. Families: n = 1, 2, 5, 20, 300 rows, 1,000 operations each. **Pull** = one statement per row; **blind** = one
statement carrying all the keys (`WHERE k IN (…)`), executed by the engine.

- **S1.** Pull ordering 1 < 2 < 5 < 20 (strict), and 300 ≥ 20.
- **S2 (Law 1 as an upper bound).** Pull failure ≤ 1 − (1 − ε)^n + 3 pp for n = 2, 5, 20.
- **S3 (Law 2).** Blind failure for n = 20 and n = 300 ≤ 2 ε; pull failure for n = 20 ≥ 5 ε.
- **S4 (Law 0).** An operation with any failed read never returns a result (0 partial results served).

## The unified claim tested across OPS1 and OPS2

**Law 1′: on every host, compounding 1 − (1 − ε)^n is an upper bound on failure (up to measurement noise), reached
when errors are independent.** OPS1 memory (independent: equal), network and ledger (below); OPS2 LLM agents and
SQLite.

Every prediction reported pass or fail; nothing changed after the run.
