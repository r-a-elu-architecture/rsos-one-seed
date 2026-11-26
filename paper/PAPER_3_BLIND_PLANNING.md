# Blind planning and the error-window law: where LLM agents break when they edit shared state, predicted in public before each run

**R. A. Elu** (ORCID 0009-0000-1456-2467) · Research paper, version 1.0 · 26 November 2026 · DOI: 10.5281/zenodo.24555298 ·
Text: CC BY 4.0; code: Apache 2.0

## Abstract

LLM agents that edit shared state (configurations, tickets, plans) commonly write the whole change set in one call as
JSON Patch, computing every new value themselves. We compare this pattern with *blind planning*: the model writes
operations that name keys and relations but never sees a state value, and a deterministic runtime computes every value
and checks every replica. Across six models from four companies, blind planning completed 318 of 320 pre-registered
tasks exactly, at 0.45–0.61× the cost per correct task; the two failures are steps the runtime refused (none silent),
on a control where long object lists met an output cap we had fixed. JSON Patch failures concentrated on whole-state requests, and we published *which step would break*
before running three model families we had never tested; it broke there on all three. We then show that one law
describes where failures fall on two very different real systems: an operation fails according to the number of
independent error windows it spans. In a real SQLite engine, failure is flat in read scope when operations are
shorter than the writer's lock cycle and climbs from 30.7 % to 72.0 % when they span many cycles; in real LLM runs,
the per-step error of one-call JSON Patch rises from 0.19 % in the first quarter of a plan to 2.33 % in the last
(Mantel–Haenszel odds ratio 12.3, 95 % CI 6.1–24.7), while blind planning stays flat. A compounding bound on failure
holds where errors are independent or positively associated and is exceeded, by the predicted amount, where
successes compete. Every prediction was hashed in public before its run; 26 of 76 agent predictions failed and are
reported. Against the strongest rival patterns (A9, two model families, tasks drawn from a public randomness beacon after
the predictions were public), blind planning was exact on 48 of 48 tasks, as was Python that sees the state; blind Python
47 of 48; one-call JSON Patch 46 of 48, with all its bad steps in the last quarter of the plan; a tool-calling agent 15 of 16
at about 100 model calls per task. All tasks, transcripts and a one-command verifier are released.

## 1. Introduction

Multi-agent workflows increasingly maintain shared state. The efficient pattern — one planner call that emits a JSON
Patch for the whole task, plus an audit — asks the model to read every value it touches and compute every new one.
Blind planning separates structure from value: the model names operations (`REHOST owner bruno chen`); a runtime
executes them. The idea belongs to the family of the dual-LLM pattern and CaMeL, which isolate data from the planning
model for security; here the goal is exactness and cost.

Contributions: (1) a pre-registered comparison on real models with every failure published; (2) failure predictions
published before testing new model families, confirmed at the named step; (3) an error-window law, with a compounding
theorem and its predicted exception, confirmed on a real database and on real LLM runs; (4) a release in which every
claim can be re-checked in one command.

## 2. Method

**Tasks.** Synthetic configuration states (S1, S2, long-task sets L1–L3; up to 300 keys and 56 change requests per
task), a robot scene no model had seen (SC1: 50 objects shared by six robots, 300 keys), and an operation set drawn
from a public randomness beacon (SC2). Requests range from setting one key to whole-state rules ("everything owned by
X is now owned by Y").

**Arms.** *JSON Patch* (B2): one planner call writes the whole task as RFC 6902 patches with literal values; one
audit call; three replicas with hash checks and repair. *RSOS blind* (X5b): the planner sees only the requests and
writes operations; a runtime computes values. Same models, seeds, integrity layer and audit rule.

**Pre-registration.** Every test was committed before its run; predictions, then code, then results; hashes in
`SEALS.md`; tasks for SC2 and ENGINE3 drawn from drand rounds fixed in advance.

## 3. Results on agents

- **Exactness.** RSOS blind: 318 / 320 tasks exact across all complete cells (A7, A8, SC1, SC2, SC2-C) on six models
  (Claude Haiku, Sonnet and Opus 5.5; Gemini 3.8 Flash; Mistral Large 4; GPT-6.2 Sol). Every JSON Patch failed step
  on the new families was state-dependent (23 of 23: REHOST, INHERIT, FUSE); blind 0. Before the new families, the
  JSON Patch failure rate per whole-state reassignment was 1.4 % (8 of 553 requests, Claude).
- **Predicted step.** Before running Gemini 3.8 Flash, Mistral Large 4 and GPT-6.2 Sol, we published that JSON Patch
  would break at task 712 or 702, step 35. It did on all three.
- **Unseen world.** SC1: blind 32 / 32; JSON Patch failed at two of five hand-overs named in advance.
- **Predicted operation.** The failure table predicted an operation before it existed (FLOW); on beacon-drawn tasks
  JSON Patch failed 14.8 % of FLOW requests (predicted ≥ 5 %); blind 16 / 16.
- **Cost.** 0.45–0.61× per correct task at 300 keys.

## 4. The error-window law

**Theorem 1.** If the per-element successes A₁…Aₙ of an operation are positively associated,
P(fail) ≤ 1 − ∏(1 − εᵢ) (Harris–FKG). **Corollary:** with negatively associated successes (elements competing for a
fixed supply) the bound can be exceeded; with exactly k of N elements unavailable, P(fail) = 1 − C(N−k, n)/C(N, n).

**Error windows.** If errors are generated by windows, an operation of duration T meets n_eff ≈ 1 + T/τ̄ windows. Short
operations fail at the single-window rate whatever their read scope; long operations accumulate windows.

**Evidence.**

| Host | Result |
|---|---|
| Independent elements (simulated) | failure equals the bound (60.6 % vs 60.4 %) |
| Bursty network (simulated) | below the bound (−7.6 pp) |
| Competing slots (simulated) | **above** the bound by +2.82 pp (≈ 7 s.e.; predicted +2.7) |
| Periodic windows (simulated) | (1 − U) + δ(n − 1)/P predicted within 0.16 pp at every scope |
| **Real SQLite** | fast reads: 28.5 → 33.7 % from 1 to 300 rows; reads spanning lock cycles: 30.7 → 72.0 % |
| **Real LLM runs (25 result files)** | JSON Patch per-step error 0.19 % → 0.49 → 1.56 → 2.33 % by quarter of the plan; OR 12.3 (6.1–24.7) stratified by operation kind; blind flat |

Read together: LLM agents writing one-call patches behave like a host whose error window grows along the plan — late
steps are computed on a state the model has itself changed. Blind planning removes the window by never reading the
state.

## 4b. The strongest rivals, predicted by the law (A9)

**Design (sealed 20 Nov 2026, 06:57 UTC; public 07:08; tasks from drand round 6657746, 08:30 UTC).** Five arms on the
same beacon-drawn tasks at 30, 102 and 300 keys: B2 (one-call JSON Patch), X5b (RSOS blind), CAv (Python, seeing the
state), CAb (Python, blind) and TC (a tool-calling agent reading what it needs, one request at a time). Families
registered: Claude Haiku 5.5, GPT-6.2 Sol, Gemini 3.8 Flash (no TC, declared in advance), Qwen2.5 7B (open weights, free
GPU). Scored: Claude Haiku 5.5 and GPT-6.2 Sol, all cells complete. Gemini 3.8 Flash completed 2 tasks before its free quota
ran out (reported, not scored); Qwen2.5 7B ran only its published smoke test (0 of 4 tasks exact for every arm at 7B,
including blind planning), so it is not scored.

**What the law predicted for each arm, before the run.** B2 reads the state once and computes every value itself, so
its errors should rise along the plan and with state size; every arm that reads the state at the moment a step runs
(X5b, CAb, CAv, TC) should stay flat. Written in advance as the outcome against RSOS: if blind Python ties blind RSOS,
the exactness comes from the principle (never show the values; read at run time), not the syntax.

**Results** (scored with the sealed `a9_analyse.py`; final 20 Nov 2026; `experiments/A9_REPORT.md` in RSOS-Language).

| Arm | Exact tasks | Silent wrong values | Model calls per task |
|---|---|---|---|
| Blind planning (RSOS) | 48 / 48 | 0 | 2.0–2.8 |
| Python, seeing the state | 48 / 48 | 0 | 1.0 |
| Python, blind | 47 / 48 | 5 steps (one task: a reversed copy inherited by four later requests) | 1.0 |
| One-call JSON Patch | 46 / 48 | 3 steps (one task), plus 2 refused steps | 2.0–2.8 |
| Tool-calling agent | 15 / 16 | 1 step | about 100 |

Ten of twelve predictions passed. Q1 (blind planning stays exact), Q2a (JSON Patch errors rise along the plan), Q2b (arms
that read at run time stay flat), Q3a and Q3b (state size hurts JSON Patch and not the blind arms), Q4 (blind Python as
exact as blind RSOS: the mechanism is blindness, not syntax), Q5b (blind RSOS cheapest per correct task at 300 keys), Q6a
(tool-calling uses at least 20 times the calls), Q6b and Q7 passed. Two failed and stand: Q5a (RSOS was not more compact
than Python) and Q6c (tool-calling's input did not grow with state size once the second family's 30-key cell was in).

**Where JSON Patch broke, it broke late.** Pooled over complete cells, its wrong-step rate was 0 of 672 steps in each of
the first three quarters of the plan and 5 of 672 (0.74 %) in the last; every arm that reads the state when a step runs
stayed flat. A second seal, written after the first cells and scored on cells that ran after it, predicted that JSON
Patch errors would fall in the second half of the plan: all four landed there (steps 45, 47, 48, 49 of 56). These are
small numbers: a direction consistent with the law, not yet a curve.

**Cost.** The tool-calling agent was exact but expensive: about 100 model calls per task against 2–3 for blind planning,
and on GPT-6.2 Sol at 300 keys about 2.0 million input tokens per task against about 51,000.

## 5. What did not hold

26 of 76 agent predictions failed, including: other model families did not propose 3× more invalid operations than
Claude (0.10 vs 0.09 per task); our failure predictor ranked steps correctly (AUC 0.95) but under-predicted their
number (7.6 expected, 22 observed); RSOS blind failed two tasks of a control set (SC2-C): planner operations for long object lists were rejected three
times and the runtime refused the step. A control without the output cap (SC2-C2) is registered and has not been run.
In A9, RSOS was not more compact than Python (Q5a) and tool-calling's input did not grow with state size (Q6c).
In the law studies, several predictions failed on sampling design (estimating ε from a separate family amplifies its
error about 9× at n = 50) and are reported with the corrected test.

## 6. Limitations

Synthetic task families (16–32 tasks per cell); the error-window analysis of LLM runs is retrospective (sealed before
analysis, on existing runs); the rival baselines in A9 run 8 tasks per cell (4 for tool-calling) on two scored model families; a guard grown from the
error-window cause (ENGINE3) is pre-registered for a beacon-drawn hold-out and has not been run.

## 7. Related work

Separating planning from untrusted values follows the Dual LLM pattern [1] and CaMeL [2], which keep the planning
model away from data it must not act on; blind planning applies the same separation to state values, for exactness
rather than security. The JSON Patch baseline is RFC 6902 [3]. Error that grows with context length and compounds over
steps is documented for long contexts [4] and multi-step composition [5]. Diagnosis-first repair of agent failures is
studied in FlowFixer [6] and DARC [7]; acceptance decided by a check the agent cannot influence, in SEAL [8].
Pre-registration in machine learning is discussed by Hofman et al. [9], and sealing a benchmark to a public randomness
beacon before its questions exist by SealedBench [10]; our task seeds come from the drand beacon [11]. The compounding
bound uses the Harris–FKG inequality [12, 13]; the odds ratios are Mantel–Haenszel estimates [14]; the database study
uses SQLite's locking model [15], an instance of lock contention in transaction processing [16].

## 8. Availability

RSOS-Language (Apache 2.0): `bench/` (JSONL tasks and scorer), `results/` (all runs and transcripts), `research/`
(the law studies), `SEALS.md`, and `python3 research/verify.py` (recomputes all opened seals and re-runs the
agent-error analysis byte for byte). Software DOI 10.5281/zenodo.24359268 (v0.4.0); the version containing A9 and `research/`: DOI 10.5281/zenodo.24401943 (v0.5.0);
results and transcripts of the agent runs: DOI 10.5281/zenodo.24358277 (v0.3.2). Companion papers: *One Selector, Many
Domains* (DOI 10.5281/zenodo.24555154) and *SRC-X.5: an open record of sealed claims* (DOI 10.5281/zenodo.24555259).

## References

1. S. Willison. *The Dual LLM pattern for building AI assistants that can resist prompt injection.* Weblog, 25 April 2023. https://simonwillison.net/2023/Apr/25/dual-llm-pattern/
2. E. Debenedetti, I. Shumailov, T. Fan, J. Hayes, N. Carlini, D. Fabian, C. Kern, C. Shi, A. Terzis, F. Tramèr. *Defeating Prompt Injections by Design.* arXiv:2503.18813, 2025.
3. P. Bryan, M. Nottingham (eds.). *JavaScript Object Notation (JSON) Patch.* RFC 6902, IETF, 2013.
4. N. F. Liu, K. Lin, J. Hewitt, A. Paranjape, M. Bevilacqua, F. Petroni, P. Liang. *Lost in the Middle: How Language Models Use Long Contexts.* Transactions of the ACL 12, 2024.
5. N. Dziri et al. *Faith and Fate: Limits of Transformers on Compositionality.* NeurIPS 2023.
6. X. Ma, Y. Wang, J. Wang, X. Xie, B. Wu, M. Li, D. Wang, Q. Wang. *Diagnosis-Driven Automatic Repair for Agentic Workflow via Symbolic Inference* (FlowFixer). arXiv:2607.02882, 2026.
7. P. Wang, Y. Hu, H. Wang, Z. Lv, X. Zhang, J. Li, J.-M. Yang, W. Wu, Y. Tong. *Diagnosis Before Recovery: Turning Agent Failures into Selective Self-Correction* (DARC). arXiv:2608.11772, 2026.
8. D. Guo, C. Cao, F. Yuan, Y. Wang, Y. Wang, D. Wang. *Self-Authored Verification Is Unreliable in Heuristic Self-Improving Agents* (SEAL). arXiv:2607.24300, 2026.
9. J. M. Hofman, A. Chatzimparmpas, A. Sharma, D. J. Watts, J. Hullman. *Pre-registration for Predictive Modeling.* arXiv:2311.18807, 2023.
10. *SealedBench: A Protocol for Freezing AI Benchmarks Before the Questions Are Known.* HackerNoon, October 2026.
11. League of Entropy. *drand: a distributed randomness beacon.* https://drand.love
12. T. E. Harris. *A lower bound for the critical probability in a certain percolation process.* Proceedings of the Cambridge Philosophical Society 56, 13–20, 1960.
13. C. M. Fortuin, P. W. Kasteleyn, J. Ginibre. *Correlation inequalities on some partially ordered sets.* Communications in Mathematical Physics 22, 89–103, 1971.
14. N. Mantel, W. Haenszel. *Statistical aspects of the analysis of data from retrospective studies of disease.* Journal of the National Cancer Institute 22, 719–748, 1959.
15. SQLite. *File Locking and Concurrency in SQLite Version 3.* https://www.sqlite.org/lockingv3.html
16. J. Gray, A. Reuter. *Transaction Processing: Concepts and Techniques.* Morgan Kaufmann, 1993.
