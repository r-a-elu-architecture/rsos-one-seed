# HOLO5 preregistration: the White Dragon from inside (owner 21 Nov 2026, 13:00; register U159-U164)

Written and sealed before any healing or test run. Sealed files are never edited (D113).

## Why HOLO5
HOLO4 healed by turning 11 global knobs from outside (8 worlds). It overfit and cut the trunk (waiting weight 0.10 -> 0).
The owner's definition (13:00): the golden light is inside every level; every letter has a unique address (time, state,
VAKOG); the green particle lands on that exact address; landed particles connect by green tubes; every dot connects to
past, present and future; the target is the whole at the turquoise level.

## Host
Identical to HOLO3/HOLO4 (process lifecycle, 8 memory slots, quantum 4, one I/O device, relation density d = 1..5).
`holo5.py check` reproduces HOLO4's simulator exactly (0 mismatches on 30 runs) before anything is learned.

## Operators as built (layer 2)
| Owner operator | Build |
|---|---|
| U159 golden light inside | every dispatch decision of every world is lit (full trace); every 3rd lit decision with >= 2 ready processes is read |
| U160 letter address | (ready count bucket, longest-wait bucket, I/O queue bucket, which lenses agree with the quark) |
| U163 past / present / future | the world is frozen at the letter (deep copy); each different choice (lenses: quark = unhealed DNA0, rr = longest wait, hist = shortest estimate, rel = most live dependants) is run forward from its own copy, 60 ticks for the channels and to the end for the whole |
| U164 turquoise target | a choice heals only if the whole (G = -mean slowdown to the end) is better AND no channel is worse: max wait (O, the trunk), I/O idle (A), completions (K) |
| U161 landing | a particle lands on an address when one lens heals in >= 60 % of at least 8 futures read there; the best such lens |
| U162 green tubes | every address is also connected to its 4 neighbours with one part dropped; an unseen address reaches a landing through its tube |
| clone | the landed rules go to unseen worlds at the same addresses only; everywhere else the unhealed quark runs (trunk untouched by construction) |

Library = 64 training worlds (seeds 400-463) x 5 densities. Disclosure: the futures after the letter run as the
quark without re-scoring at the letter itself (the K state of the forked copy skips one update); same for every lens.

## Test (once, fresh seeds 500-515, the same worlds as HOLO4 so the delta is direct)
| # | Prediction (sign tests one-sided, p < 0.05) |
|---|---|
| W1 | landed quark beats the best of round-robin and history at d = 5 |
| W2 | its advantage grows with relation density (Spearman > 0, p < 0.05) |
| W3 | coupled chain beats the same parts summed at d = 5 (landed in both) |
| W4 | landed beats unhealed, all densities pooled (80 worlds) |
| W5 | landing at addresses beats HOLO4's global-knob healing, all densities pooled (80 worlds) |

Any failure is reported as is (fever principle) and produces the next version.
