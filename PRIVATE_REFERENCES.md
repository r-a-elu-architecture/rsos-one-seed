# References to the private research record

Some files in this repository cite paths under `corpus/`. That folder is the owner's private research record
(conversation transcripts and design notes). It is not published, by decision D85. The citations are kept because they
show where a hypothesis or a design came from, and because several of them are inside pre-registrations and seals,
which must stay byte-identical to what was committed before each run.

| File | What it cites | Effect for a reader |
|---|---|---|
| `seal2/PREREG_SEAL2.md`, `seal2/SEAL_SEAL2.txt` | the 24 Nov turns that set the SEAL2 hypothesis | the one hash line for that private file cannot be checked; every code hash can |
| `experiments/structure/PREREG_STRUCTURE2.md`, `experiments/structure/SEAL_STRUCTURE2.txt` | the same 24 Nov turns | as above |
| `experiments/PREREGISTRATION_H2.md`, `PREREGISTRATION_A3B.md`, `PREREGISTRATION_A7.md`, `PREREGISTRATION_A8.md`, `experiments/holo1/PREREG_HOLO1_DESIGN.md` | the owner's words or decisions that set each test; sealed design passes | provenance only; no test reads the private files |
| `research/sealed/seed/SEED_V1.md`, `research/sealed/roots/PREREG_T2B.md` | where the private copy of each sealed note is kept | provenance only |
| `protocol/SEAL_SRCX5_PUBLIC.txt` | where the private launch forecast is kept | provenance only; every hash line can be checked |

Removed from the public release: `experiments/genealogy/` (its inputs are drawn from the private record).
Source comments in `src/rsoslang/` and `spec/LANGUAGE.md` now describe the private design notes instead of citing
their paths.
