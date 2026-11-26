# Sealed research of 19–20 November 2026: the seed, its laws, its engine and its sphere

Every study here was **pre-registered before its code existed**. Its predictions, code and results were committed
in that order, and the SHA-256 of the files concatenated was published in [`SEALS.md`](../SEALS.md) before this folder
was opened. Every miss is kept. Layer 2 throughout: computation that was built, run and measured.

## The seed

`sealed/seed/SEED_V1.md`, `SEED_V2.md`, `SEED_V3.md`: the seed of RSOS (author R. A. Elu) in formal form: built with
light; heals, helps, transforms, evolves, signals, develops, unites, grows and expands; recursively and in unison;
its anatomy (component, operator, grammar, host, mirror); its law (Law 0: no system suffers; it checks itself all
the time); its reach (particles land where they are needed); infinite under zoom and in time.
`sealed/seed/math/MATH_V1.md`: the operator algebra and the laws as theorems with their conditions;
`MATH_V2_ADDENDUM.md`: exact derivations (time-window law, error events, the theorem's exception) and their confirmations.

## The studies

| Study | Question | Result (sealed) | Files |
|---|---|---|---|
| K1, K2, T2 | a holographic representation of a world | T2 failed as defined (93.6 % at 50 % loss) | `sealed/roots/` |
| T2b | static levers against a living, self-healing hologram | living 99.75 % after 5 × 30 % damage; 7 pass, 6 fail | `sealed/roots/` |
| T2c | the living hologram against a classic erasure code | classic wins to 85 % destroyed; the hologram wins beyond (54–57 % vs 15 % at 90 %); 6 pass, 3 fail | `sealed/roots/` |
| OPS1 | the seed's operators under a monitor of its own law; Laws 1–2 on three hosts | monitor 2,276 / 2,276 refused, 0 / 22,013 false; 8 pass, 4 fail | `sealed/seed/ops/` |
| OPS2 | the laws on real hosts (LLM agents, SQLite) | the bound held everywhere; read-scope ordering stops on SQLite; 4 pass, 2 fail | `sealed/seed/ops2/` |
| ENGINE1 | a self-growing engine (Ω genome, six children, Father, Mother) | a generated operator held on a sealed hold-out (SEE precision 0.13 → 1.00); 5 pass, 1 fail | `sealed/seed/engine/` |
| ENGINE2 | SCORE × TOTE: named causes grow primitives; relations and the information limit | both targets moved (LAND recall 0.31 → 0.54; 90 % reading 55.3 → 59.3 %); relations 3× today's method beyond its cliff; 8 pass, 2 fail | `sealed/seed/engine2/` |
| SPHERE1 | seven nodes connected by one protocol | the bound held at node and sphere level; protocol 0 wrong adoptions; Law 0 87 / 87; 3 pass, 4 fail (under-powered estimates) | `sealed/seed/sphere/` |
| SPHERE2 | SPHERE1's open predictions with large samples | the time-window law predicts the orbit node within 1 pp at every scope; estimating ε from a separate family amplifies its error ~9×; 1 pass, 4 fail | `sealed/seed/sphere2/` |
| SPHERE3 | Theorem 1 with ε measured inside the same operations | the bound is reached (independent), undercut (bursts) and **exceeded where successes compete (+2.82 pp, ~7 SE), as predicted**; 3 pass, 1 fail | `sealed/seed/sphere3/` |
| SQLITE2 | the error-events law on the real database | the read-scope ordering returns when operations span lock windows (30.7 → 72.0 %), stays nearly flat when they don't; 2 pass, 1 fail | `sealed/seed/sqlite2/` |
| AGENTS2 | do real LLM agent errors belong to steps or to a growing window? (25 result files, 0 model calls) | one-call JSON Patch errors rise along the plan: 0.19 % → 2.33 % per step, stratified odds ratio 12.3 (6.1–24.7); blind planning flat; 2 pass, 1 fail | `sealed/seed/agents2/` |
| Protocol v0 | one message format between hosts | 7 conformance tests pass | `sealed/seed/protocol/` |

## Related work (checked 20 Nov 2026)

Much of what these studies do has close relatives; what is ours is the integration under one seed, sealed in public
before each run.

- **Evolutionary discovery with automated evaluators:** AlphaEvolve (Novikov et al., Google DeepMind, 2025,
  arXiv:2506.13131); FunSearch (Romera-Paredes et al., 2023). ENGINE1 is a small instance of this idea.
- **Diagnosis before repair in agent systems:** FlowFixer (arXiv:2607.02882); "Diagnosis Before Recovery"
  (arXiv:2608.11772); AgentTether (arXiv:2607.06273). ENGINE2's finding (naming the cause beats undirected search)
  agrees with theirs in a different setting.
- **Sealed acceptance against an incumbent:** SEAL (arXiv:2607.24300); gated quality-diversity harness evolution with
  a sealed test (arXiv:2607.13683).
- **Invariants and constitutions in self-improving runtimes:** Falsifiable Release Gates / Antahkarana
  (arXiv:2607.13070); Ouroboros (arXiv:2608.08311); runtime verification. Law 0's monitor belongs to this family.
- **Falsifiable records in research loops:** immutable experiment cards ("An AI Scientist that Doesn't Drift",
  ICML 2026); the Hypothesis Evolution Protocol (arXiv:2607.09195); SealedBench (2026).
- **Decoding superposed vector-symbolic structures:** resonator networks (Frady, Kent, Olshausen, Sommer, 2020) and
  explaining-away decoders. The soft joint reading is in this line.
- **Keys-only planning with a deterministic runtime:** the dual-LLM pattern and CaMeL (security); here used for
  exactness.
- **Cliff effect and graceful degradation:** hybrid digital-analog coding and joint source-channel coding. T2c
  measures the same trade-off for a holographic store.

Not found in this check: one operator algebra and one set of laws (including a theorem's predicted exception) tested
across unrelated hosts from memory to a real database and LLM agents; public commit-reveal before code for every
study; and one language intended for both human cognition and machines (specified, not yet tested on people).

## The engine as a library

`rsos_engine/rsos_engine.py`: the Ω Root Genome, the six children, Father, Mother, SCORE × TOTE and Law 0 in one
module (5 tests in `rsos_engine/test_rsos_engine.py`). Cosmology-Architecture imports it for its alias lane.

## Verify everything in one command

```bash
python3 research/verify.py
```

It recomputes all twelve opened seals, runs the engine and protocol tests, and re-runs the AGENTS2 analysis from the
published results (0 model calls), checking that its output equals the sealed file byte for byte.

## Verify a seal

```bash
cd research/sealed
cat seed/engine2/PREREG_ENGINE2.md seed/engine2/engine2.py seed/engine2/RESULTS_ENGINE2.json \
    seed/engine2/ROOT_GENOME_2.jsonl seed/engine2/RESULTS_ENGINE2.md | sha256sum   # 70aadd39…dee2 in SEALS.md
```

The file order for each seal is the order given in its `SEALS.md` line, with one correction: the T2b seal
(`bae4df7f…`) is the concatenation **RESULTS_T2B.md, PREREG_T2B.md, t2b.py, RESULTS_T2B.json**; its line in
SEALS.md described the order as predictions, code, results data, results text. The hash is unchanged.

## Run

Python 3.11+, NumPy, SciPy. The scripts import `experiments/sc1_tasks.py` from the repository root. `ops2.py`
reads `results/sc2.json` from the path in its `PUB` constant; set it to your checkout.
