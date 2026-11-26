# X1 pre-registration: painting a system built outside this session (written before running)

**System:** the cue framework's own agent system and repair loop (`rsxv/rsxv/archetypes.py`, public repo, read-only):
- six agents (Raven, Bear, Eagle, Leopard, Tiger, Lion) in a dependency graph;
- each agent has three modules (perceive, decide, act);
- errors pass downstream (70% of the worst input's error);
- repairs cost budget and can fail (85%) or damage (10%).

**Painting:** the graph is painted automatically (`painting/graphs.py`): agents as objects, inputs as flows.

**Gesture:** an observer touches the system. Which repair strategy runs is decided **only by the entry side's fixed
meaning** in the RSOS Language (D80), compiled from the program:

| Program | Core meaning | Strategy in the cue framework |
|---|---|---|
| `TOUCH observer ON system AT surface` | interface_only | `local_repair`: each symptomatic agent retries its own modules |
| `TOUCH observer ON system AT side` | lateral | `local_repair(blame_upstream=True)`: ask the neighbouring input |
| `TOUCH observer ON system AT top` | supervisory_entry | `meta_repair`: the Override from the meta position |

**Faults:** 300 seeds. Each injects 1–2 faults at random agents and modules (severity 0.8; half silent). Budget 6.

| # | Hypothesis | Pass rule |
|---|---|---|
| H1 | The three meanings select three strategies with different measured outcomes | Fixed rates differ pairwise, or health differs |
| H2 | Entering from the top (supervisory) repairs better than touching the surface (cue framework design, AGENTS.md §6) | Fixed rate top > surface; 95% bootstrap CI of the paired difference above 0 |
| H3 | Reported, no threshold | Top vs side |
