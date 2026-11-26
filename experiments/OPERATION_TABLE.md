# The operation table: Core operations ordered by what they read and write

Fixed 19 Nov 2026, 08:35 Vilnius (06:35 UTC), before any SC1 result was seen and before any operation in the gaps was
built. Decision D102. The registry (`registry/operators.json`) lists the operations; this table orders them by one
principle so that the gaps become visible, and states what a law derived from the measurements predicts for each gap.
The table counts as a law only when a predicted gap is built, run and confirmed (SC2 is the first).

## 1. The two axes

**What the operation reads from the state** (rows): nothing · one key · two keys · a condition on one key · the whole
state (a scan for every key that matches).

**What it writes** (columns): one key, a literal the planner names · one key, a value computed from the state · many
keys.

## 2. The table

| Reads ↓ / writes → | one key, literal | one key, computed | many keys |
|---|---|---|---|
| nothing | `set`, `delete` | | **gap A** `set_all` |
| one key | | `copy`, `derive`, `multiply` | |
| two keys | | `sum_into` | |
| a condition on one key | `select_if` | | **gap B** `set_where` |
| the whole state (scan) | | **gap C** `aggregate_where` | `reassign_where` (literal) · **gap D** `derive_where` (computed) |

`state_digest` and `reconcile` are functions over the whole state and sit outside the table.

## 3. The law, from the measurements

Every one-call JSON Patch step (arms B2 and B2s) and every RSOS blind step (X5b) of A7 and A8, by operation kind, from
the 19 result files `results/a7_results_*.jsonl` (all models, SC1 excluded; computed 19 Nov, 0 model calls):

| Reads | Operations | JSON Patch steps failed | RSOS blind steps failed |
|---|---|---|---|
| nothing | `set`, `delete` | 0 / 3,063 (0.00%) | 0 / 2,703 |
| a condition | `select_if` | 0 / 788 (0.00%) | 0 / 696 |
| one key | `derive` (incl. copy), `multiply` | 10 / 7,125 (0.14%) | 0 / 6,477 |
| two keys | `sum_into` | 2 / 1,193 (0.17%) | 0 / 1,096 |
| the whole state | `reassign_where` | **19 / 823 (2.31%)** | **0 / 718** |

**Law (empirical):** the failure rate of one-call JSON Patch rises with how much of the state the model must read
itself to write the patch, and jumps by an order of magnitude when it must scan the whole state; RSOS blind planning
does not read the state and stays exact on every row. A second factor: computing a value per key adds failures to
reading it (one key computed 0.14% vs one key literal 0.00%).

## 4. Predicted properties of the gaps

| Gap | Form (Core) | Example in the robot scene | JSON Patch, predicted | RSOS blind, predicted |
|---|---|---|---|---|
| **A** `set_all` | `set_all(field, value)`: every key with that field := value | "Every object's grip is now soft." | low: no reading, but many entries to list; ≈ `set` per entry, failures from omissions only | exact |
| **B** `set_where` | `set_where(field, value, cond_field, equals)`: for every object whose `cond_field` = `equals`, `field` := value | "Everything in the lab now rests on the shelf." | scan with a condition on another field: ≥ the `reassign_where` rate | exact |
| **C** `aggregate_where` | `aggregate_where(dst, field, cond_field, equals)`: `dst` := sum of `field` over matching objects | "Set rover.load to the total weight of rover's objects." | scan + read every match + sum: the highest of all rows | exact |
| **D** `derive_where` | `derive_where(field, cond_field, equals, add, max)`: for every matching object, `field` := min(int(field) + add, max) | "Move every object of rover one cell right (x plus 1, capped at 9)." | scan + read + compute per match: **above** `reassign_where` | exact |

Ordering predicted for JSON Patch failure rates: C > D > B ≥ `reassign_where` > one key computed > nothing.

## 5. The first test

Gap D is pre-registered as **SC2** (`experiments/PREREGISTRATION_SC2.md`): it is the closest gap to the measured
failure (`reassign_where`) and adds exactly one factor (a computed value per match), so it tests the second part of
the law directly. The RSOS name of each new operation is chosen by the language's author from its symbols before it is
built; the Core names above are neutral working names.
