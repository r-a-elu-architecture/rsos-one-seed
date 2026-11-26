# SQLITE2: the error-events law on the real database (layer 2, real host), sealed before any code

Written 20 Nov 2026, ~08:10 Vilnius. Private. OPS2 found SQLite's failure flat in read scope (errors belong to the
writer's lock windows, not to elements). The error-events law (MATH_V1 §5) predicts that the ordering **returns** when
an operation lasts longer than the writer's cycle, because it then spans several independent lock windows.

## Design

Same engine and writer as OPS2 (SQLite 3.53.1, rollback journal, one writer process committing every 10 ms, reader
busy timeout 0). Two reader speeds, interleaved at random in one run: **fast** (no delay between reads, as OPS2) and
**slow** (1 ms sleep after every read, so 300 reads last ≈ 300 ms, many writer cycles). Families 1, 2, 50, 300 reads;
600 operations per family and speed. An operation fails at its first locked read.

## Predictions

| # | Prediction |
|---|---|
| Q1 | fast: flat, |failure(300) − failure(1)| ≤ 5 pp (OPS2 replicated) |
| Q2 | slow: ordering returns, failure(1) < failure(50) < failure(300), and failure(300) ≥ failure(1) + 20 pp |
| Q3 | slow, failure(50) and failure(300) ≤ the compounding bound 1 − (1 − ε₁)^n + 3 pp (Theorem 1: lock windows are positively associated) |
