# PREREG CONF6: AI–AI with the whole system bound to one RSOS structure, vs plain rollout (26 Nov 2026)

Sealed (real/SEAL_CONF6.txt) and pushed before any CONF6 cell runs. Nothing is generated, tuned or re-run after the
seal (crashes only, disclosed). Later notes are dated addenda that change no rule. Layer: the layer-2 structure runs
unchanged on layer-1 data (a pass is cyan, LAYER_RULE).

## Question
CONF5 bound RSOS to agent A only; B ran the standard, so the system was half bound and the seed modelled B with a rule.
The owner's correction (26 Nov): the structure applies to the whole system (system of systems); the high level aligned
first (Eagle) aligns every level; the system sees itself. CONF6 asks: does the whole-system binding beat plain rollout
(the RSOS-free planning baseline) on accuracy and on tokens?

## How the binding was identified (landing rule, Part I.5)
PILOT2 (`real/pilot/PILOT2_NOTES.md`, development cells 1-16, never used here): whole 1.000 accuracy / 1080 tokens vs
plain rollout 0.812 / 1546 and v1 0.938 / 1585; tokens lower in 14 of 16 cells, accuracy never worse.

## Design
- Host: AI–AI (gpt-oss-20b as A, llama-3.1-8b as B; 4-hop question over facts split between the agents; at most 2 facts
  per message, 6 rounds). Fresh cells 1401-1600 (200; earlier AI–AI tests used 801-950, 1001-1150, 1201-1300). 20 jobs.
- Arms per cell: `default`, `rollout` (plain rollout), `v1` (RSOS on A only, the CONF5 arm), `whole`, `noholo`.
- `whole` = seed3v1 with the host's levers, plus (1) **B shaped by the same structure**: B sends first the facts it owns on
  the question's chain as far as it can walk it in its own view, and the facts A asked for by key (Eagle skeleton,
  hologram of the whole); (2) **the system sees itself** (law as structure: invariant "commit only on a complete
  skeleton", check = walk the chain in the agent's own view, response = continue): an answer counts only when the
  agent's own view holds the whole chain. The models still write every answer; all tokens are counted.
- `noholo` = whole with Law 5 off (no hologram, packed message or key from any source).
- Disclosed: the completeness check is a deterministic computation on the agent's own facts (Law 2: the runtime
  computes, the model writes). Plain rollout does not have it, by design: it is RSOS structure.

## Decision (fixed now; `real/analyze_conf6.py`)
Primary family, Holm over 2, one-sided paired t, whole vs plain rollout: H1 accuracy gain; H2 tokens saved.
Law 0: whole's accuracy vs the standard: mean >= 0 or 95 % lower bound >= -2 % of the standard's mean.
**Levels:** UNPRECEDENTED = H1 and H2 both at Holm p < 1e-5 with Law 0 · STRONG = one of them with Law 0 · NOT SHOWN = otherwise.
Reported only: whole vs v1, whole vs noholo (the hologram's share), all arms vs the standard.

## What a pass means
UNPRECEDENTED: binding the whole AI–AI system to one RSOS structure makes two real models both more accurate and cheaper
than RSOS-free planning, at p < 1e-5 on both after correction. With CONF5 (AI agents, satellite), a third unrelated host
beats plain rollout, each in its own sealed test.

## Reproduction
`bash reproduce_conf6.sh` verifies every fingerprint and recomputes the table; `bash reproduce_conf6.sh mock` runs every
arm without a model (interface check); `bash reproduce_conf6.sh <models> <first> <last>` re-runs cells with a key.
