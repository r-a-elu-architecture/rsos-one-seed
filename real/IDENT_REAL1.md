# Step 1 identification: REAL1, the one seed in ten real hosts (24 Nov 2026 ~13:10, UTC+02:00). No build before the owner's OK.
Owner 12:15-12:41: move to layer 1 (the real world, connected to layer 2 by flows); one strategic test; the same seed must
show itself in every domain and in money (less spending, faster computation, more growth). Budget: OpenRouter key
`rsos-seed-test`, credit limit $20 (owner, 13:04). Calibration: phase 3 (4 models x 300 tasks x 5 arms) cost $8.45.

## The seed (one file, one hash, unchanged in every host)
The layer-2 structure of STRUCTURE1-6: each step the host offers branches (present action, the unit's own past and planned
future actions, focused actions per part, coupled parts, the host's level); the seed chooses the branch whose own future is
best (Law 4, K.2), under the host's budget, with the membrane (never worse than the host's default on its bound).
## The binding (same interface for every host; sealed before the run; nothing tuned per host after the run)
`units()` the parts with needs; `budget()` landings per step; `branches(state)` the candidate actions; `future(state, a)`
the host's own short future after action a (its simulator, or its own model for data hosts); `default(state)` the host's
standard action (the membrane's bound); `cost(a)` the resource it spends.
## One measure everywhere
R = result per unit of resource, seed vs the host's standard method, at equal or better quality; plus growth (result over
time). Pass per row (fixed before the run): seed > standard method in >= 2/3 of the row's cells and mean > 0.

| # | Domain | Real host (tool / data) | Units, budget | What the seed chooses | Own future | Standard method | Resource | Runs |
|---|---|---|---|---|---|---|---|---|
| 1 | AI | agents on real models via OpenRouter (tasks of phase 3, new seeds) | reasoning branches; token budget per task | which branch gets the next call | the model's own next-step proposal (one short call) | ReAct, self-consistency | tokens = $ | laptop |
| 2 | AI-AI communication | two real models solve a split-information task over a limited message channel | message parts; message budget | what to send now (road 8 beam: parts by need) | receiver's predicted use | send the full context / summary | tokens, messages | laptop |
| 3 | AI-human communication | public human dialogue corpus (real human turns), model reply under a length budget | parts of the reply; length budget | what to answer first | predicted next human turn coverage (fixed rule, proxy: no live humans) | standard reply | tokens | laptop |
| 4 | Quantum computing | Qiskit + Aer simulator, real benchmark circuits | circuits / observables; shot budget | where the next shots go | simulated estimate error after the shots | uniform, variance-proportional | shots | here |
| 5 | Space communication | real satellite orbits (CelesTrak elements, Skyfield): real ground-station contact windows | data items; bytes per contact | what to downlink in each real pass | the real future pass schedule | FIFO, priority queue | bandwidth | laptop (download) |
| 6 | Energy | pvlib real solar + load data, battery model | hours; storage and dispatch budget | when to store / dispatch | the battery model over the next hours | rule-based dispatch | kWh, cost | here |
| 7 | Economics / finance | inventory / supply simulator on public demand series | items / sites; capital budget | where limited stock or capital goes | the simulator's next periods | base-stock policy | capital, stock-outs | here |
| 8 | Robotics | Gymnasium control tasks (physics simulator) | joints / actions; control-effort budget | where control effort goes | the simulator's next steps | standard controller | energy, steps | here |
| 9 | Neuroscience | public neural recordings (DANDI / Allen open data) | channels; sensing budget per time step | which channels to read now | held-out prediction of the signal | uniform, variance-based sampling | samples read | laptop (download) |
| 10 | Life science | the 8 real biology hosts of ORG-REAL1 (repo) | as ORG-REAL1 | as ORG-REAL1 | as ORG-REAL1 | best native method | as ORG-REAL1 | here |

## Plan
1. Seed file + the ten bindings (here; laptop parts as scripts). 2. One quick test per row on development data; a failed
row -> back to this table (rule 0.1). 3. One combined seal (code, bindings, baselines, cells, pass rules, max cost $20),
pushed. 4. One confirmatory run (laptop rows with the hidden key; here rows here). 5. The table: one seed, ten domains,
R per domain; a projection of R x each sector's spend, labelled as a projection. 6. White paper from sealed results only.

## Honest limits, fixed now
- What a row shows is the flow of the seed into THAT host; a row that does not carry is reported as such.
- Row 3 is a proxy (real human dialogue data, a fixed scoring rule), not live people.
- Rows 4, 6, 7, 8 run on real tools that are simulators of the physical host (real circuits, real data, real physics
  engines), not the physical devices; real hardware (IBM Quantum, a real battery) is the next step.
- Estimated cost: $3-10 of the $20 key limit (rows 1-3). Build time: about a day here. Run: hours.
