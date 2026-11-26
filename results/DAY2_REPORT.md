# Day 2 report: executable semantics and the re-run of chat 1's experiments

**Gate (from the roadmap):** pierce ≠ attach and the move + pierce interaction reproduced with seeds and hashes.
**Outcome:**
- pierce ≠ attach: **passed**.
- The move + pierce interaction: **not reproduced as positive**; it was negative in 40/40 worlds.
- Seeds and hashes: **passed**. A rerun gives identical `results_sha256`.

Pre-registration: `experiments/PREREGISTRATION_DAY2.md`, committed before running (`450a9e8`). Rules:
`spec/SEMANTICS.md`. Reproduce: `./reproduce.sh`.

## What now runs

Operators have their own effects in the simulation runtime (16 runtime tests):
- pierce goes through the layers, both ways, and reaches neighbouring processes;
- attach makes one dependency;
- touch at the top supervises every surface module (D80); a declared binding (`local_contact`) changes it to one
  link, and a search candidate is chosen by the runner;
- rotation rewires many links at once;
- overlay hides half of each;
- region ≠ point, whole ≠ part, and path direction matters;
- black → grey changes function; heal, beam down, flows by direction, route by state, dot (adds, does not replace)
  and re-host (a different result per host) all run.

## R-003: re-implementation of C1-EXP-003 (40 worlds, unseen environment)

| Hypothesis (from the chat) | Our result | Pass |
|---|---|---|
| H1 move + pierce interaction positive (chat: 40/40, +0.1825) | **Negative in 40/40, mean −0.1029** [−0.1210, −0.0869] | **No** |
| (post hoc, not pre-registered) the same without the 0.002 cost per link | −0.0149 [−0.0330, +0.0011]; positive in 17/40: no consistent interaction | — |
| H2 ablation: no exchange between paintings → interaction 0 | 40/40 zero (harness check) | Yes |
| H3 pierce ≠ attach | Different in 40/40; **attach scored higher in 39/40** (mean −0.129) | Yes (different); pierce was not better |
| H4 one rotation changes many links (chat: median 46 vs 1) | Median **114** links changed (68–156) vs 1 for an explicit edit | Yes |
| H5 encode → decode; relabelled glyphs | 256/256 and 256/256 (a codec check, not a discovery) | Yes |

## R-004: re-implementation of C1-EXP-004 (40 worlds, thermal environment, utility at the sinks)

| Hypothesis (from the chat) | Our result | Pass |
|---|---|---|
| Structure: 4 points → 7 links → 49 property assignments | **4 → 7 → 49**, exactly as in the chat | Yes (structure) |
| H6 full triangle > single point (chat +0.1078 vs −0.0075) | Triangle better in 10/40; mean +0.0044 [−0.0092, +0.0199] | No |
| H7 internal modules > whole car (chat −0.0075) | 10/40; same numbers as H6, because in this layout the whole car and the point both select the car's single surface module (a layout limitation) | No |
| H8 forward > reversed (chat −0.0175) | 13/40; mean +0.0013 [−0.0449, +0.0472] | No |
| H9 diverse-archive search > random (chat +0.0399, 12/12) | Archive − random = −0.0321 [−0.0758, +0.0036]; archive better in 5/12. Held-out means: random 0.159, evolution 0.124, archive 0.127 | No |

## Hard truth

**What reproduced is the language as structure.** The operators exist, they compile and they behave differently:
- a rotation rewires about a hundred links in one move;
- the car-seat program has exactly the 4 → 7 → 49 shape of chat 1;
- the codec is exact;
- the same program always gives the same result.

**What did not reproduce is that these operators help.** In worlds whose modules have **random** functional
properties, none of chat 1's functional advantages appear:
- the move + pierce interaction is negative;
- pierce scores below attach;
- triangle, internal selection and forward direction show no consistent gain;
- diverse-archive search does not beat random search.

The chat's 40/40 and 12/12 came from worlds ChatGPT authored together with the operators, and their code was never
captured.

**What this means.** Our earlier caution is now a measurement:
- results produced in a world designed with the operator say little about other worlds;
- an operator has no value in general. Its value depends on the host's functional structure: random hosts give no
  systematic gain.

This is the same conclusion as chat 2's law ("the host decides"), now from the negative side. It also sets the job
for day 3:
- test the operators in hosts with **real structure** (the wine, digits and cancer datasets; the documented models);
- check whether the gains appear there, against baselines.

## Files

- Runtime: `src/rsoslang/runtime/` (`model.py`, `execute.py`, `codec.py`)
- Tests: `tests/test_runtime.py`
- Experiments: `experiments/r003.py`, `experiments/r004.py`
- Results with hashes:
  - `results/R-003.json`: `results_sha256` e6c41adc…
  - `results/R-004.json`: `results_sha256` 560ba06f…
