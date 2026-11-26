# REAL1 binding brief (for every builder; fixed 24 Nov 13:25)
Repo: /home/claude/rsos-multimodal-world (branch core-v1). Read real/seed.py (the interface in its docstring) and
real/host_toy.py (a minimal example). DO NOT edit seed.py, host_toy.py, or anything outside your own files.
Write per row: real/hosts/<row>.py (a class implementing EXACTLY the interface: reset, done, default, branches, valid, step,
fork(state, j), objective, report, horizon, samples) and real/hosts/<row>_quick.py (runs `seed.run(host, cell, "seed")`
and `seed.run(host, cell, "default")` on development cells 1..4 and prints result, resource, R for both; nothing else).
Rules:
1. default(state) = the domain's STANDARD method (named in real/IDENT_REAL1.md), implemented faithfully and as strong as
   the standard is. It is both the baseline and the membrane bound. Never weaken it.
2. Layer-1 rule: fork(state, j) is the host's OWN MODEL with randomness independent of the real step (seed it from
   (cell, t, j, a constant)); it must never copy the real rng or any future data. For data hosts the model may only use
   data up to the current time.
3. branches(state): 2-6 focused actions (resource concentrated on one part) and, if the host has parts that drive each
   other, 1-2 coupled actions. Same budget as the standard action (valid() enforces the budget).
4. report: {"result": the domain's quality measure, "resource": the resource spent (tokens, shots, kWh, bytes, effort...)}.
   objective(state) = the RESULT only (no division by resource; no hidden bonus). The resource is a constraint: valid()
   keeps every action within the same budget the standard method has. (Fixed 13:45: a result/resource objective rewarded
   withholding work - space row: value per MB up 3-4x while value delivered fell. The pass rule is now a Pareto win per
   cell: result >= standard AND resource <= standard, at least one strictly.)
   Refined 14:05 (before any seal): where the domain prices its resource INSIDE the result (energy: net $ after wear;
   economics: profit after carrying cost) the resource is already counted once; requiring resource <= standard as well
   would count it twice. Pass per cell = result > standard for priced rows; Pareto (result >= standard AND resource <=
   standard, one strictly) for rows whose resource is not priced into the result (tokens, bytes, shots, samples,
   effort). Each row's file states which kind it is.
   Refined 14:15 (before any seal): a third kind, FIXED-BUDGET rows, where both methods are given the same budget by the
   host itself and unused budget is simply lost (quantum: shots; neuro: samples per step; space: each pass's contact
   capacity - the pass happens whether or not it is filled). Pass per cell = result > standard at the same budget.
   Kinds: priced (energy, economics) and fixed-budget (quantum, neuro, space): result > standard; free-resource rows
   (AI agents tokens, AI-AI tokens, AI-human tokens, robotics effort): Pareto.
5. Keep each episode small enough that `_quick.py` finishes in under 3 minutes on 1 CPU here (choose horizon, samples,
   episode length accordingly; write the choice and why in the file's docstring).
6. Network: here only pip (pypi) and GitHub work; other downloads are refused. If a row needs a public dataset that is not
   reachable here, write `<row>_fetch.py` for the owner's laptop and, for the check here, a clearly marked stand-in
   generated from the same structure (docstring: "STAND-IN for the interface check only, never for results").
7. Model calls (LLM rows): use experiments/agents/llm.py (keys from environment only; never in files). Here there is no
   key: implement a `mock:0` path for the check and say which OpenRouter model ids the laptop run uses (cheap: e.g.
   openai/gpt-oss-20b, meta-llama/llama-3.1-8b-instruct).
8. pip install with --break-system-packages if needed. Do not commit or push; the lead reviews and commits.
Return: the files written, the quick-test output (both modes, 4 cells), the standard method you implemented and its source,
and anything that is a stand-in or a proxy.

## REAL2 additions (24 Nov 19:35; owner: "land where it is needed")
A. LAW 4 LANDING interface (seed.land; read real/seed.py): implement in the host
   landings(state, action) -> list of landing ids (the budget units of the action, at a sensible granularity: e.g. a
     reasoning-branch call, a block of shots on one observable, a kWh block in one hour, an order unit on one item, one
     data item in a pass, a control-effort chunk, one channel read, one fact/word in a message, a batch group per class)
   without(state, action, L) -> the action without landing L (less resource)
   targets(state, action, L) -> up to 3 parts where L could go instead (highest need first, from the host's own state)
   retarget(state, action, L, T) -> the action with L moved to T (same resource)
   Keep landings few enough that a quick test still runs in minutes (the seed tests each landing in the own futures).
B. PLAIN ROLLOUT is built into seed.run(mode="rollout"); "seed_noland" = REAL1's seed. Quick scripts print all four modes:
   seed, seed_noland, rollout, default (+ the strongest method below).
C. STRONGEST METHOD per row (a new standard="strongest" mode of the host, faithful, same forecasts/data, no look-ahead):
   energy: scenario-based stochastic MPC (scenarios from the history up to now); space: a look-ahead downlink planner
   (exact or MILP/knapsack over the known future passes); economics: stochastic inventory optimisation (scenario /
   dynamic-programming order-up-to with capital budget); AI agents: confidence-based early stopping of self-consistency
   (CGES/ReASC style, no token log-probs if unavailable: answer-agreement posterior). Other rows: their current standard
   is already the strongest available (state it).

## REAL3 (24 Nov 20:35): bind your row to the composed seed (real/seed3.py; read its docstring fully; do NOT edit it)
Layer 2 (AI-RSOS) rebuilds the frame; layer 1 is where it lands. Do not accept the real world's frame as a limit: find
the levers the standard method does not use, with the SAME real tool and the SAME budget.
Add to your host (keep everything that exists; REAL1/REAL2 modes must give identical numbers):
  primitives(state) -> [(family, name, action)]: the library primitives (map Part I.2, P1-P8) bound to this host's levers;
     family = "P1".."P8"; e.g. P4+P5 = your strongest/scenario optimiser's action as one candidate ("P4P5").
  frame(state) -> [(family, name, action)]: the row's FRAME levers (below), family = "F:<short name>".
  coupled(state) -> bool: True when this decision's parts drive each other (then the seed lands the action as a whole).
Quick script: per development cell print modes seed3 (seed3.run), seed, rollout, default, strongest; cells 1-8 (fewer if
slow; under ~10 min here); for LLM rows mock:0 here (real models run in the cloud).
Row frame levers (owner/map; these are the point of REAL3):
  ai_agents: BLIND PLANNING (the model names operations/keys once; the runtime computes values; see README_PUBLIC.md
    "Blind planning" and experiments/A7/A8 code) + HOLOGRAM CONTEXT (send keys + state digest, not the transcript) +
    O-trace PLAN REUSE across tasks of the same type (pool) + vote only where the tree says uncertain.
  ai_ai: HOLOGRAM MESSAGE (structure: keys + digest, not sentences; the receiver computes) + shared trace (never resend
    what the other holds) + carrier with route by loss.
  ai_human: HOLOGRAM REPLY (the reply carries the whole conversational state: what they see / hear / need) + READY gate.
  quantum: JOINT MEASUREMENT (one setting informs many observables: group qubit-wise commuting observables; shots on a
    shared setting count once) + O trace across steps.
  space: HOLOGRAM CODING of the backlog across passes (frames that serve all missing items under loss) + exact planner
    as P4P5 + tubes between ground stations.
  energy: P5 over the real-past scenario tree (SOC dynamic programming) + P2 price on wear + coupled hours.
  economics: P4P5 (the stochastic optimiser) + RELATIONS between items (pooling / substitution where the data allow)
    + O trace of demand surprises.
  robotics: P5 over the whole trajectory (short-horizon trajectory optimisation as one candidate) + trace of disturbances.
  neuro: O trace + RELATIONS between channels (cross-channel prediction from the real past) + read where the whole learns most.
  biology: DATA LANDING (train only where needed; check the earlier artefact: does accuracy really rise when groups are
    withheld, on held-out test data?) + P8 vote of futures.
