# PREREG STRUCT1: does the RSOS structure itself carry, without host-written levers? (25 Nov 2026, ~12:50, UTC+02:00). Layer 1. Confirmatory.

Written, hashed (`real/SEAL_STRUCT1.txt`) and pushed BEFORE the run, on the owner's instruction of 12:27 ("one decisive
sealed test of the STRUCTURE ... switch, not build ... claim levels fixed now, unchangeable after the run").
Why: the independent review of the REAL3 paper (paper rev. 2, Appendix A) found that most REAL3 gains come from
host-written levers (primitives P1–P8 and frame levers such as `F:blind`). This test switches those off and asks whether
the general structure alone beats both the standard and plain rollout.

## Arms (every cell, all existing modes; `cloud/struct1_unit.py`)
- **structure**: `seed3.run(h_off, cell, "seed3v1")` = the sealed REAL3 seed, unchanged, on a host whose
  `primitives(s)` and `frame(s)` return nothing (a flag on the host instance; `real/seed3.py` is not edited). What acts:
  own-future valuation over model futures (TREE ≥ 8 forks); time branches (present, own past −1/−2, own plan +1/+2);
  own-plan and standard continuations (whole-plan valuation through the own plan); Law 4 landing per part, or the whole
  when the host says its parts are coupled; the membrane; the observer (apoptosis, P6 ordering of what worked).
  It chooses from the same action set as plain rollout: the standard action plus the host's native `branches`.
  The policy continuation of REAL3 applies to host levers only, so in this arm it does not act.
- **seed3v1**: the full sealed REAL3 seed (host levers on).
- **rollout**: plain rollout, `seed.run(h, cell, "rollout")`: standard action plus native branches, valued over the
  same forks with the standard continuation only.
- **default**: the row's standard method.
- **strongest**: the row's strongest method where it has one (inventory: scenario stochastic LP; satellite: look-ahead
  MILP; AI agents: CGES-style early-stopping self-consistency). AI–AI and AI–human: the standard is the strongest.
Leak fix: before every arm the seed trace and the AI-agent plan stores (`PLAN_POOL`, `EXEC`, `TRACE`) are cleared, and
every cell runs in a fresh process. The REAL3 FIX1 calc wrapper is applied (an unparsable formula is a plan error).

## Rows, models, cells
Five rows: AI agents (gpt-oss-20b; standards ReAct and self-consistency = 2 units), AI–human (Mistral Small 3.2),
AI–AI (gpt-oss-20b with Llama 3.1 8B), inventory (economics host), satellite downlink (space host).
Fresh cells **301–308** (never used in development, REAL1 or REAL3), 4 pairs per row, one pair per job, all jobs in
parallel. One look. Development cell 1 was used once, before sealing, for a crash check only (no result read).
Disclosed: satellite orbit offsets repeat every 6 cells (`cell % 6`); AI–human native branches include "mention" slots
that target the word-overlap score (both structure and rollout have them).

## Measures and decision (fixed now; `real/analyze_struct1.py`)
- Per unit, two one-sided paired-t tests over its 8 cells: **structure vs default** and **structure vs rollout**.
  Inventory and satellite (fixed budget): result gain. AI rows (free resource): resource saved (tokens).
- **Holm** at family-wise one-sided α = 0.025 over all primary tests (6 units × 2 = 12).
- A test passes if Holm rejects it and, for AI rows, the result is not worse (mean result gain ≥ 0, or its 95 % lower
  bound ≥ −2 % of the comparator's mean result).
- A unit passes if both its tests pass; a row passes if any of its units passes.
- **Claim levels, fixed now and unchangeable after the run:**
  - **UNPRECEDENTED:** structure beats both the standard and plain rollout, after Holm, in **at least 4 of the 5 rows**.
  - **STRONG:** the same in **2–3 rows**.
  - **NOT SHOWN:** fewer than 2 rows.
- Secondary (reported, no level): full seed vs strongest; structure vs full seed; full seed vs standard; rollout vs
  standard (95 % intervals).
All units are reported as they come. A crashed job may be re-run once, disclosed; nothing else is re-run.

## Budget (checked 12:35)
GitHub Actions: 8,234 job-minutes this month on this repository's private runs (≈ $42–50 of the $60 cap, depending on
included minutes). This run: about 20 jobs; estimated 500–700 job-minutes (≈ $4–6), dominated by satellite. OpenRouter:
not readable from the session; the workflow prints the key's usage and limit before the AI rows run and stops them if
less than $1 is left.
