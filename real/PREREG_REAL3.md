# PREREG REAL3: one composed RSOS seed, ten real domains (25 Nov 2026, ~05:10, UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius). Layer 1. Confirmatory.

Written, hashed (`real/SEAL_REAL3.txt`) and pushed BEFORE the run; owner "yes" 04:49. Runs on GitHub machines
(workflows `rsos-real3-s1`, `rsos-real3-s2`); results pushed to branch `cloud-results` (`real3/`). Development record:
`real/quick_logs/`, `real/results_cloud/real3v2/`, cloud runs 45474488429 (REAL3 v1), 45520822292 and 45523940403
(REAL3 v2 waves 1 and 2).

## Hypothesis
One composed RSOS seed (`real/seed3.py`, mode `seed3v1`; unchanged in every row: VAKOG order; time branches and the
tree of model futures; Laws 0–4 landing per part or whole; library P1–P8; frame levers; shared trace with ordering and
observer; every primitive and frame lever valued as a whole policy over the horizon) beats each domain's standard
method on that domain's real host, and is reported against the domain's strongest method where one exists.

## Which seed (rule fixed 25 Nov 01:15, applied before this run)
One version for all rows: REAL3 v2 (all RSOS operators, mode `seed3`) if it won more row-cells than v1 on the
development cells, else v1 (ties → v1). On the finished development cells v2 did not win more (quantum 1–3,
economics 2–2, neuroscience 2–2, space 1–0, robotics 0–1, AI rows mixed); wave 2 was stopped early (04:49) to keep the
GitHub budget for this run, so the rule was applied on the finished cells. **Seed = v1 (`seed3v1`).**

## Rows, hosts, standards, strongest
As in REAL1 (`real/PREREG_REAL1.md`, `real/IDENT_REAL1.md`, `real/HOST_BRIEF.md`), with the REAL3 decisions:
quantum joint-setting shots cost their hardware width (`COST`; width-free variant not run); AI–AI pack off; biology
per-class landing in every host (`coupled = False`); bounded model calls (`real/hosts/llm_bounded.py`; a failed call is
counted, not retried forever). Strongest method: energy, economics, space (own hosts with `standard="strongest"`),
AI agents (CGES early-stopping self-consistency); quantum, AI–AI, AI–human: the strongest is the standard; robotics,
biology, neuroscience: no separate strongest method (compared with the standard only).
Models (OpenRouter): AI agents gpt-oss-20b and Llama 3.1 8B; AI–AI gpt-oss-20b with Llama 3.1 8B; AI–human Llama 3.1
8B and Mistral Small 3.2.

## Cells (fresh; never used in development or in REAL1)
Stage 1: cells 201–208 in every row and model. Stage 2 (only units the rule leaves undecided): cells 209–216.
Neuroscience: the recording has 12 windows; windows 1–4 were development cells, so REAL3 uses windows 5–12 (8 cells),
one look only. Disclosed: windows 9–12 were REAL1's fresh windows (seen with the REAL1 seed only, never used to build
REAL3). Space: the orbit offset repeats every 6 cells (`cell % 6`); the on-board data differs per cell.
Each cell runs in its own process with an empty seed trace, so every cell is independent and re-runnable alone.

## Measures and pass rules (fixed now; `real/analyze_real3.py`)
Unit = row × model × standard. Paired per cell (same cell, same random draws for every method).
Kinds: priced / fixed-budget rows (energy, economics, quantum, neuroscience, space, biology): result gain.
Free-resource rows (robotics, AI agents, AI–AI, AI–human): resource saved at equal result.
1. Per test: cells won (priced/fixed: seed result > standard; free: Pareto, result ≥ and resource ≤, one strictly).
2. Mean gain per cell with its two-sided **97.5 %** paired-t interval (two looks, Bonferroni: 2.5 % one-sided overall).
   SHOWN (priced/fixed): mean result gain > 0 and lower bound > 0.
   SHOWN (free): mean resource saved > 0 with lower bound > 0, AND result not worse: mean result gain ≥ 0 or its lower
   bound ≥ −2 % of the standard's mean result.
3. Sequential: after stage 1 (8 cells) a unit is SHOWN (stop), NOT SHOWN if the upper bound of its deciding quantity
   ≤ 0 (stop), else UNDECIDED → stage 2; after stage 2 the decision uses all 16 cells.
4. Against the strongest method: the same measures, reported (secondary; no stage 2 on this comparison alone).
5. The cross-domain claim counts the rows with at least one SHOWN unit against the standard.
All units are reported exactly as they come; nothing is changed after the run. A unit that crashes on a code error is
reported as crashed; any re-run of it is under this seal and disclosed. Cost caps: OpenRouter key $20, GitHub Actions
budget $60 (stage 1 estimated ~$10, stage 2 ≤ ~$10).
