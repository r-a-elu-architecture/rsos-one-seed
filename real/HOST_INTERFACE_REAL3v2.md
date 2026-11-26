# REAL3 v2 host interface: seed operators (25 Nov 2026; owner 00:13 "go")

One assembled seed (`real/seed3.py` + `real/seed3_ops.py`), the same operators in every row. A row binds by adding a
few OPTIONAL methods to its host. Every hook is optional: a missing hook makes only the operators that need it
"not bound" (listed in `run()["ops_bound"]` with the reason); nothing is forced, and `seed3.run(host, cell, "seed3")`
works for a host with none of them. Do not edit `seed.py`, `seed3.py`, `seed3_ops.py`. REAL1/REAL2 modes
(`seed.run(..., "seed" | "seed_noland" | "rollout" | "default")`) are untouched. `seed3.run(host, cell, "seed3v1")`
reproduces REAL3 v1 exactly (checked on Toy/ToyLand cells 1-4).

## Hooks (all optional; `s` = state, `a` = action, `p` = part id; part ids must be hashable)

| Hook | Returns | Semantics |
|---|---|---|
| `parts(s, within=None)` | list of part ids | the decision's parts; `within=p` gives p's sub-parts (ENTER depth 2; omit the argument if the host has no sub-parts) |
| `merge(s, {p: a_p, ...})` | action | apply each `a_p` on its part only; dict order = which part gets the step's resource first; parts not named take the standard action; must be made feasible by `valid` (the seed calls `valid` after) |
| `part_action(s, a, p)` | action | not needed: the seed uses `merge(s, {p: a})` |
| `part_objective(s, p)` | number | the part's own value now (higher = better); enables COLOUR, HEAL, CONTAIN and the generic shape |
| `focus(s, p)` | action | the whole step's resource on part p (BEAM; HEAL and ENTER use it when present) |
| `shape(s)` | hashable (str()-able) | compact state key (COMPRESS, INHERIT); default = rank pattern of part objectives + rounded spread + colours |
| `joint(s)` | `[(name, action)]` | native joint actions (FUSE) |
| `carry(s, a)` | action | `a` with the step's unused resource carried to the next step (the host's state holds the bank) |
| `map_part(s, a, p_from, p_to)` | action | the pattern of `a` on `p_from` re-expressed on `p_to` (RE-HOST) |
| `op_of(family)` | common op name or None | extends the seed's table host family -> common operator name (TRANSPLANT); None = use the seed's table (`P1/P3 -> heal, P2 -> contain, P4/P4P5 -> fuse, P5/P6 -> inherit, P7 -> explore, P8 -> vote, F:* -> frame, focus -> beam`) |

Minimum useful binding: `parts` + `merge` (binds PIERCE, OVERLAY, FUSE, ENTER). Add `part_objective` (COLOUR, HEAL,
CONTAIN, COMPRESS, INHERIT), `focus` (BEAM), then `carry`, `map_part`, `joint`, `shape` where the row has them.

## Which operators need which hook

| Operator | Hooks | Fully generic? |
|---|---|---|
| ROOMS (Eagle / Owl / Associated / base) | none | yes |
| ZOOM (scales H/2, H, 2H; block of 3) | none | yes |
| TRANSPLANT (shared pool by common names, file in/out) | none (`op_of` optional) | yes |
| VOTE (P8 gate on any override) and MEMBRANE (Law 0) | none | yes |
| PIERCE, OVERLAY, FUSE, ENTER | parts, merge (ENTER depth 2: parts(s, within)) | needs the part hooks |
| COLOUR, HEAL, CONTAIN | parts, merge, part_objective | needs the part hooks |
| COMPRESS, INHERIT | shape, or parts + part_objective | needs a state key |
| BEAM 1 / BEAM 3 | parts, merge, focus | needs focus |
| CARRY | carry | host only (the bank is the host's state) |
| RE-HOST | parts, merge, map_part | host only (how one part's action reads on another part) |

Meanings of each operator: `real/seed3.py` docstring (one place).

## Environment

- `SEED3_POOL_IN=path.json`: the TRANSPLANT pool (and COMPRESS shape table) loaded at import (another row's trace).
- `SEED3_POOL_OUT=path.json`: saved at the end of every `run()` (the path is returned in `run()["pool_saved"]`).

## Report fields added by `run(host, cell, "seed3")`

`ops_bound` (per operator: bound / not bound and why), `ops_used` (times an operator was the chosen action; colour /
rooms / transplant = steps they routed), `ops_tried` (valued under the budget), `ops_passed_membrane`, `vote_vetoed`,
`rooms`, `colour_counts`, `zoom_scale_decisions` (scale -> count), `enter_depth`, `rollouts_v1`, `rollouts_ops`,
`op_fallback` (hook errors on forks, the standard used instead), `inherit_entries`, `shape_keys`, `pool_loaded_from`,
`pool_saved`, `seconds`.

## Worked example: `real/host_toy.py`, class `ToyOps`

Toy: 12 units lose level each step; budget K = 3 refills per step; standard = refill the 3 lowest units.
`ToyOps(ToyLand)` adds (Toy and ToyLand are unchanged, so REAL1/REAL2 numbers are identical):

```python
def parts(s, st, within=None):         # thirds of the units; within a third: its two halves
    if within is None: return [tuple(range(g * s.N // 3, (g + 1) * s.N // 3)) for g in range(3)]
    h = len(within) // 2; return [tuple(within[:h]), tuple(within[h:])]
def merge(s, st, d):                    # named parts' units first (dict order), standard units on the unnamed parts
    out, named = [], set()
    for p, a in d.items(): out += [u for u in s._units(a) if u in p]; named |= set(p)
    out += [u for u in s.default(st) if u not in named]
    return list(dict.fromkeys(int(u) for u in out))          # valid() truncates to the budget
def part_objective(s, st, p): return float(st["x"][list(p)].mean())
def focus(s, st, p): return sorted(p, key=lambda i: st["x"][i])[:s.K]
def joint(s, st): return [("one-per-part", [min(p, key=lambda i: st["x"][i]) for p in s.parts(st)])]
def carry(s, st, a): ...      # refill only units below 0.6, marker "C" banks the unused refills (bank <= K)
def map_part(s, st, a, pf, pt): ...   # the k-th lowest unit of pf -> the k-th lowest unit of pt
def op_of(s, fam): return None
```

For example, at a step where the third (4, 5, 6, 7) is failing, HEAL builds `merge(s, {(4,5,6,7): focus(s, (4,5,6,7))})`
(three refills there first), CONTAIN builds `merge(s, {(0..3): a*, (8..11): a*, (4..7): standard})`, PIERCE probes
`merge(s, {p: a*})` for each third in the forks and applies a* only on the third that gains most. Every candidate is
valued in the same 8 model forks as v1, must be >= the standard action (Law 0) and must beat a* in the room's comparison
and in a majority of the forks (P8) before it replaces a*.

Run: `SEED3_POOL_OUT=/tmp/pool_toy.json python3 -c "import sys; sys.path.insert(0,'real'); import seed3, host_toy as T;
print(seed3.run(T.ToyOps(), 1, 'seed3'))"`.
