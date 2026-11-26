# PREREG STRUCT1, addendum: the exact candidate sets (written 25 Nov 2026, 12:45, UTC+02:00)

**Timing, disclosed:** STRUCT1 was sealed at commit `925abf5` and its run (45596832492) started at 12:37. The owner's
request to list the candidate sets arrived at 12:39. This addendum documents what the sealed code already does; it
changes no rule, no code and no cell. It was written before any STRUCT1 result was seen.

## Shared by "structure" and "rollout": the standard action plus the host's native branches (`host.branches(s)`)
| Row | Native branches (identical in both arms; from `real/hosts/<row>.py`) |
|---|---|
| AI agents (`ai_agents.py`) | `focus-b<b>` (next step on branch b), `restart-b<b>`, `open` (new branch), `stop` (commit an answer), `cross` (coupled: one branch drives another); at most 6 |
| AI–human (`ai_human.py`) | `unit-<k>` / `unit-<k>c` (mention the words of one unit of the turn, now or carried), `top` (mention the top-ranked words), `link` (link a question to a context word); at most 6 |
| AI–AI (`ai_ai.py`) | `focus_<relation>` (send only facts of one relation), `ctx` (only facts about entities already in context), `chain` (coupled: own linked facts together) |
| Inventory (`economics.py`) | `prebuild`, `lean`, `focus_big`, `focus_small`, `focus_short`, `pair` (rationing patterns of the capital budget) |
| Satellite (`space.py`) | `focus_<part>` (earliest-deadline-first within one data class), `urgent` (urgent items first) |

## Removed in "structure" (present only in the full seed `seed3v1`)
Everything returned by `host.primitives(s)` (library patterns P1–P8, including P4P5 = the strongest method's action)
and `host.frame(s)` (frame levers, e.g. `F:blind`, `F:reuse`, `F:holo*`, `F:otrace*`). The flag replaces both methods
on the host instance with functions that return nothing. Checked on development cell 1 before sealing: the structure
arm chose no `P*` or `F:*` candidate in any row.

## Added by the structure (the thing under test; absent from "rollout")
- Time branches: the unit's own past actions (−1, −2) and own planned actions (+1, +2), offered as candidates.
- The own-plan continuation: each candidate is valued both with the standard continuation and with the unit's own plan.
- Law 4 landing: after the choice, each landing (`host.landings`) is tested with and without it and withheld or
  retargeted by need; skipped when `host.coupled(s)` says the parts drive each other (then the whole lands).
- The observer: a family whose realised advantage is negative in its last 3 uses while predicted positive is switched
  off for 5 steps; families that worked are tried first.
- The membrane (never worse than the standard action in the same forks) holds in both arms.
Both arms use the same model forks (TREE ≥ 8) and horizon.
