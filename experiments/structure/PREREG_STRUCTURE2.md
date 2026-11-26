# PREREG STRUCTURE2: the one structure + relations; does the layer-2 table fill? (24 Nov 2026 ~11:05, UTC+02:00)
Layer 2. Development quick test: no colour. Written, hashed and pushed BEFORE the run. Owner turns and answers:
`corpus/chat-6/turns_24nov_structure.md`.

## Hypothesis (owner, 09:54-10:53)
Every unit, at any scale, holds its past, present and future; only the structure changes (more or fewer branches).
One structure, placed once, fills every open layer-2 row; relations are the same structure recombined across units.

## Structure (code `structure2.py` on `structure1.py`)
Branches: space (rooms, organs), lineage (parents' trajectories), time (t-2 .. t+2), relations (#1 neighbours in LE,
#2 lungs+heart+kidney coupled branch, #3 pair relation from all 7 shades). One operator: Law 4, the organism's own
future to the end of the world (K.2 unchanged). Seed world 30 ticks.

## Cells
Laws: shades 4, 10 x seed 6670. Organs: shades 4, 10 x seed 6720. Development seeds only.

## Checks (all must pass for TABLE_FILLED; fixed now)
- Laws (LAWS6 analyze, unchanged criteria): EXACT, L0, L1', L1, L2, C2, C1, L4, L3, PR, RC.
- LE_relations: every (shade, channel) row within tolerance at windows 2, 4, 8.
- L5_relations: cross-entropy with the relation < without, for shades 4 and 10 (fit on the other 6 shades).
- Meaning M1: structure > best single room, both cells.  D B1: child > best parent, both cells.
- E E1: structure in the living host > best native, both cells.  E2 (vs v3): reported, not a check (as in organs.py).
## Rule
Results reported as they come, filled or not. A failed check is not re-run with variations: back to step 1 (0.1).
A pass is development evidence only; colours come from SEAL2 (fresh seeds, full sample) on the owner's laptop.
