# SQLITE2 results (layer 2, real host), private

Predictions: `PREREG_SQLITE2.md` (commit 4720cc3). Code: `sqlite2.py` (commit 14521a9, before any result). Data:
`RESULTS_SQLITE2.json`. Run 20 Nov 2026, ~08:15 Vilnius, on SQLite 3.53.1 with a real writer process; 600 operations
per family and speed, interleaved at random.

## Strongest finding

**On the real database, the ordering returns exactly when the error-events law says it should.** With fast reads (an
operation shorter than the writer's cycle) failure stays nearly flat; with slow reads (an operation spanning many lock
windows) it climbs with read scope:

| Reads | 1 | 2 | 50 | 300 |
|---|---|---|---|---|
| fast | 28.5 % | 29.7 % | 31.5 % | 33.7 % |
| **slow** | **30.7 %** | **33.0 %** | **38.2 %** | **72.0 %** |

What an error belongs to (a lock window) and how many windows an operation spans decide its failure, on a real engine.

## Predictions: 2 pass, 1 fail

| # | Result |
|---|---|
| Q1 fast flat within 5 pp | **fail**: +5.17 pp (28.5 → 33.7 %); nearly flat, just over the margin |
| Q2 slow ordering returns, +20 pp | **pass**: 30.7 < 38.2 < 72.0 %, +41.3 pp |
| Q3 slow within the compounding bound | **pass**: 38.2 % and 72.0 % against bounds of 100 % (lock windows are positively associated) |
