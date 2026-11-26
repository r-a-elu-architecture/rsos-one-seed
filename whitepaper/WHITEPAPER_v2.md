# RSOS: an executable spatial-symbolic language for human–AI and AI–AI communication

**R. A. Elu** (ORCID 0009-0000-1456-2467) · Whitepaper v2 · approved by the author 17 November 2026 · v2 DOI: 10.5281/zenodo.24320392 ·
Concept DOI (all versions): 10.5281/zenodo.24304403 · v1: 10.5281/zenodo.24304404 · Software: RSOS Language 0.2.0,
10.5281/zenodo.24317658 · Text: CC BY 4.0; code: Apache 2.0

Every result is stated as measured and pre-registered. Failures are reported next to the successes and are part of
the result.

## Abstract

RSOS is a programming language whose programs are spatial and symbolic compositions (objects, places, flows,
beams, colours, dots, rooms, senses). Its operators (heal, beam, contain, compress, inherit, transplant, re-host,
fuse, pierce, route by state, …) act on any host: a person, a team, an AI agent, an organisation or a physical system.
v1 described the language and fixed the predictions of its first real-host test. v2 reports that test and three more,
run on real LLM agents (about 11,800 model calls in total), plus the first human test.

1. **Self-healing communication (A1).** On a three-agent workflow, the palace protocol used 0.15× the channel tokens
   of full-state JSON. It finished more tasks exactly (7/8 vs 5/8) and repaired 24/24 injected drifts with zero model
   calls and 38 tokens each. A model-based checker spent 6.9–10.2k tokens and about 13 s per repair.
2. **Knowing cross-domain redesign (A2).** Given only the host's parts, their weaknesses and a cross-domain library,
   the White Dragon engine re-derived the palace mechanism on its own and placed it first. It cut errors by 63%, and
   its predicted gain was within 16% of the measured gain. The same landing budget spent blind made the host worse.
3. **Head to head against compact protocols (A3, A3b).** Re-implementations of Slipstream-style anchors and
   ACCP-style deltas compress well, but neither keeps every copy of the state true. The palace as run in A1 kept the
   copies true but was 1.84× the size of the anchors. The hologram palace that the White Dragon designed for A3b used
   **0.64× the channel tokens of the anchor protocol (0.55× in BPE tokens)**. It kept **16/16 tasks exact with every
   copy true**, healed **48/48 drifts with zero model calls and zero channel tokens**, and accepted **0 of 1,140
   truncated messages**. It is the only protocol tested that is both smaller than the anchor protocol and keeps every
   copy true. The 5× target was missed: what remains is free prose that must be restored byte-exactly.
4. **Human input (HT1).** Free-typed symbols were not faster than the author's own shorthand and dropped elements. In
   response, an RSOS keyboard layer was built and passed a functional check (12/12). Its test (HT2) follows a learning
   phase.

## 1. What changed since v1

| | v1 (17 Nov 2026, morning) | v2 |
|---|---|---|
| Real-host evidence | None; A1 pre-registered | A1, A2, A3, A3b on real agents; HT1 on a person |
| Pre-registered predictions on real hosts | 0 | 27, of which 18 pass and 9 fail (§7, §8) |
| Comparison | Our own baselines | Also re-implementations of two published compact protocols |
| White Dragon | Simulated growth (E1, F1b) | Knowing transplant (A2) and protocol design (A3b) on a real host |
| Human side | Not measured | HT1 (failed); keyboard layer built and checked |
| Failure record | Listed | Mapped: 23 failures, their cause and next test (§8) |
| Software | Code released | RSOS Language 0.2.0 with its own DOI, CI, mission kit |

## 2. The language

- **Components.** Every symbol is a component with properties, functions, processes, interfaces, levels, a host
  binding, a colour state and a position.
- **Operators** act on components. The **grammar** is spatial and sequential: the order of objects in a scene,
  paths, regions from the centre, depth and layers. The sequence is the program.
- **Hosts decide behaviour.** The same bundle behaves differently on a body, a person, a team, an agent or a planet,
  and the compiler checks host compatibility.
- **Mental-model construction.** Cognition is built as an architecture. A house is the whole; rooms are states (the
  view from above, observing, from inside); objects are the models run in a state; each part of an object carries one
  model (a perspective plus a composition of components). The same house can hold external systems, so one
  architecture serves human cognition and AI workflows.
- **Interfaces.** Programs compile to paintings and back (`docs/editor.html`). The keyboard layer (§6) emits whole
  components and operators per key.

Specification: `spec/LANGUAGE.md`, `spec/REFERENCE.md`, `spec/SEMANTICS.md`. Compiler: `rsoslang` (108 statements,
107 operator rows).

## 3. Governance inside the language

Person-facing operations require consent (compiler error E018). Standing consent is valid only inside a declared
network with members and laws (E021 otherwise). The Spine (seven virtues) blocks predicted harm (E019). These checks
run at compile time; they are not policy added afterwards.

## 4. The communication layer

- **Palace.** Parties share a book of meanings; a message is a short sequence of anchors into it.
- **Green dot.** Each message carries a check value of the state it refers to, so a silent change (drift) or a cut
  is detected, not misread.
- **White Dragon heal.** On drift, only the changed part is repaired from the shared book, without a model call.
- **Hologram palace (new in v2).** The whole state is held behind every reference: a message carries only what the
  receiver cannot already reconstruct, plus the green dot. Opening the message (decoding) restores the full state
  identically on every side. The format is designed by the White Dragon, not hand-tuned (§5, A3b).

## 5. The White Dragon engine

The engine decomposes a host into parts with functions. For each part it selects the best cross-domain mechanism,
the depth at which to land it (surface, inside, structure) and the order of the landings, and it predicts the change
in efficiency and effectiveness. Operator: `TRANSPLANT … FROM … DEPTH … ORDER … GAIN …`. The ordered landings form a
3D connection map, which is the build plan. On the real hosts in v2 the engine runs as one design call to a frontier
model (`claude-opus-5-5`) given the host's parts, measured weaknesses and the target. Agents never see the engine.

## 6. The keyboard layer

HT1 showed that typing is the bottleneck: symbols had to be spelled out, and elements were dropped. The keyboard layer
(`docs/keyboard.html`) maps keys and chords to complete components, operators, perspectives, states, depths, orders
and directions, so a program is entered at the speed it is seen and no required slot can be left out silently.

**Functional check (amendment 1 to HT2, automated, before any human run).** Twelve targets were keyed by a headless
browser, compiled and decoded blind from the RSOS code alone. The published page passed 8/12; the check found one bug
(an operator key overwrote a finished model, which is exactly the element-dropping the layer exists to prevent).
After the fix it passed 12/12, and the code-only decode recovered 88/89 fields (0.989). HT2 itself (sealed novel tasks
against plain text) runs after a learning phase with a pre-registered plateau gate.

## 7. Results on real hosts

Host for A1–A3b: planner → worker → checker, all `claude-haiku-5-5`, 14 change requests on a 30-line state, 3
injected drifts per task. Every experiment was pre-registered and committed before it ran. Every message and model
call is recorded, and each results file carries a hash. Channel tokens use a regex proxy; every compactness pass
below also holds in BPE tokens (o200k).

### A1: palace vs three strong baselines (8 tasks, 1,522 calls; results sha256 `d224abbf…`)

| | Palace | JSON full state | Structured output | Summaries + retrieval |
|---|---|---|---|---|
| Exact success | **7/8** | 5/8 | 5/8 | 0/8 |
| Channel tokens per task | **2,563** | 17,311 | 24,425 | 4,561 |
| Drift caught | **24/24** | 24/24 | 23/24 | 0/24 |
| Per repair: channel tokens / model tokens / time | **38 / 0 / 0.15 ms** | 875 / 6,894 / 13.8 s | 1,607 / 10,214 / 13.0 s | — |

Predictions: 5 of 6 pass. **P2 failed:** a checker that remembers the last approved state also caught all drift. The
palace's distinguishing property against a full-state baseline is the cost and determinism of detection and repair,
not the detection rate. Against the memory pattern common in production, detection itself differs: 24/24 vs 0/24.

### A2: the knowing White Dragon redesigns a weak host (6 tasks per stage, 5,687 calls; sha256 `8916f4de…`)

Host: A1's summaries + retrieval configuration (5.83 wrong lines per task). The knowing map landed, in order: a
memory journal with per-line check and restore (from DNA mismatch repair and ledger reconciliation), a full view for
the worker, a full view for the checker, and a commander's-intent procedure for the planner.

| Arm | Wrong lines after 4 landings | Change | Billed tokens |
|---|---|---|---|
| **Knowing** | **2.17** | **−63%** | +20% |
| Blind | 8.17 | worse | +95% |
| Weighted (F1b rule) | 3.33 | −43% | +72% |

Predictions 4 of 4 pass: knowing beats blind and weighted; gain on 3 of 4 landings; predicted total gain within 16% of
measured; the map's order beats a shuffled order. **The engine re-derived the palace's green dot and heal on its own,
from other domains, and placed it first.** Two independent routes reached the same mechanism.

### A3: head to head with compact protocols (16 tasks × 4, 3,200 calls; sha256 `ff058345…`)

D and E are re-implementations from the published descriptions of Slipstream (shared concept anchors) and ACCP
(deltas with sequence numbers), not the original systems.

| | Palace (A1 protocol) | JSON | D · anchors, Slipstream-style | E · deltas, ACCP-style |
|---|---|---|---|---|
| Exact success | **16/16** | 4/16 | **16/16** | 1/16 |
| Every copy true at the end | **16/16** | 4/16 | 0/16 | 1/16 |
| Channel tokens per task | 2,699 | 17,442 | **1,468** | 2,773 |
| Drift healed with 0 model calls | **48/48** | 0/48 | 0/48 | 0/48 |
| Drift left in some copy | **0** | 0 | 40 | 6 |
| Truncations silently accepted | 0 | 0 | 13/1,150 | 99/1,955 |

Predictions: 2 of 4 pass (R2 healing, R3 success). **R1 failed:** the palace was 1.84× the size of D, because of
formats it inherited from A1 (a verbose verdict on every approval), not because of its integrity layer. **R4 failed**
on channel tokens against E (38 vs 96 per repair), although once model work is counted the palace's repair costs 0.9%
of E's. The anchor protocol keeps the authoritative state right only because no agent reads the drifted copy; 40 of
48 corruptions stayed latent in it.

### A3b: the hologram palace (16 tasks × 2 new arms, 1,374 calls; sha256 `0ae0d031…`)

Two arms, pre-registered before any code: **H-dragon**, a compact protocol designed by the White Dragon in one call
with its own predicted size, and **H-copy**, hand-built from the anchor protocol's formats plus the green dot.
Palace, D and E are re-used from A3 after all 48 of their runs replayed through the current harness with 0 mismatches.

| | Palace | D · anchors | H-copy | **H-dragon** |
|---|---|---|---|---|
| Channel tokens per task (BPE) | 2,699 (3,131) | 1,468 (1,860) | 1,290 (1,695) | **932 (1,023)** |
| × D, regex / BPE | 1.84 / 1.68 | 1 / 1 | 0.88 / 0.91 | **0.64 / 0.55** |
| Exact success | 16/16 | 16/16 | 12/16 | **16/16** |
| Every copy true | 16/16 | 0/16 | 12/16 | **16/16** |
| Drift healed with 0 model calls | 48/48 | 0/48 | 47/48 | **48/48** |
| Channel tokens per heal | 37.9 | — | 2.0 | **0** |
| Truncations silently accepted | 0 (A3) | 13/1,150 | 0/1,175 | **0/1,140** |

Predictions for H-dragon: 5 of 7 pass (B1 smaller than D; B3 full integrity; B4 success ≥ D; B5 better than H-copy;
B7 heal cost). **B2 failed:** the target was 0.2× D, and H-dragon reached 0.64×. **B6 failed:** the engine predicted
321 tokens per task and 932 were measured (−66%). H-copy: 2 of 5 pass; its four inexact tasks were model edit errors
that the checker approved. Every prompt the agents saw was identical across arms, so the codec did not cause them.

**Why 5× was missed is measured exactly.** Every place where the engine landed fell close to the floor: verdicts
854 → 32 tokens per task (27×), edits 196 → 44, forwards 187 → 49, heal 114 → 0. Together these cost 124 tokens per
task, 8.4% of D. **87% of what remains is the planner's free prose (808 tokens),** which must be restored byte-exactly
and rarely repeats a sentence shape within a task. The engine had flagged template coverage as its own main
uncertainty; it was right about where the risk lay and wrong about its size.

### Claim, worded to its evidence

In pre-registered tests on real LLM agents, a protocol designed by the RSOS White Dragon engine used 0.55× the BPE
channel tokens of a Slipstream-style anchor protocol. It kept every copy of the shared state true in 16/16 tasks,
against 0/16 for the anchor protocol, and repaired every injected drift without a model call or a channel token. This
is an exceptional measured result. It is not unprecedented in its parts: check values and restore-from-journal are
old ideas in databases and file systems. **To our knowledge, RSOS is the first agent communication language in which
detection and in-place healing are part of the protocol, and the first in which the protocol itself was designed by
a cross-domain engine whose choices were tested against blind alternatives.**

## 8. Human input: HT1 and the failure map

**HT1 (one person, the author; sha256 `e1f8266b…`).** The author entered six of his own models as typed symbols (S)
and as text (P). S was faster on 0 of 5 timed tasks while also at least as accurate: **K1 failed**. Mean accuracy was
0.88 for S and 0.96 for P. Where S was faster it had dropped an element. The protocol deviated in one way that changes
the reading: P was written as shorthand, so HT1 compares two compressed forms by the same person.

**Failure map (`experiments/FAILURES_MAP.md`).** All 23 pre-registered failures to date are listed with their cause
and the next test. Of the first 20, 14 are failures of blind choice: fixed rules, random growth, resending, or typing
by hand. Two are already fixed, and four are threshold misses or need people. A3b has since answered two of them (A3
R1 and R4). It added three: B2, the prose floor; B6, the engine's size prediction from two example steps; and H-copy's
model edit errors. Each remaining "the engine applies" entry is a hypothesis to pre-register, not a result.

## 9. Earlier results (simulation and code, unchanged from v1)

| Test | Result |
|---|---|
| C1 palace messages | 280/280 decoded exactly; drift detected 366/366 |
| T7 structure vs names | meaning carried by structure 98.3% vs names 3.3%; **10% relation noise: 47.5% (failed)** |
| T8 one program, two runtimes | a person's session and an agent (accuracy 0.488 → 0.762) from the same program |
| V1 sense keys (simulation) | one rich sense channel opens the anchored state 0.90–0.92 vs a name key 0.18 |
| H3c evolve-healing (simulation) | quality −0.19 → +0.67; harmful copies 4.95% → 0.60% |
| E1, F1b White Dragon growth (simulation) | deficit targeting 2.5×; **entry reinforcement +0.02 (failed)** |

## 10. Related work and what is new

**Earlier work by the author.** RSOS was first described in R. A. Elu, *The Recursive Symbolic Operating System
(RSOS): A Framework for Symbolic Cognition, Override Protocols, and Recursive Identity Engineering*, whitepaper
v1.0/v1.1, August 2025 (timestamped with SHA-256, OpenTimestamps and IPFS). It set out the seed of the work (healing,
transformation, signalling) and applications in therapy, performance and resilience, development and AI research.
Its claims of validation were internal and were not independently tested; the pre-registered programme reported
here replaces them. The 2025 papers keep their own licences; the RSOS Language code is Apache 2.0 and this text
CC BY 4.0.

- **Slipstream** maps messages onto shared concept anchors and reports 82% fewer tokens (41.9 → 7.4 on average).
- **ACCP** (IETF Internet-Draft, April 2026) specifies a compact frame format, an intent ontology, and state
  compression with checkpoints and delta encoding; it reports 60–90% fewer tokens than natural language or JSON.
- **AACP** (IETF Internet-Draft, 2026) is a typed coordination format that encodes recurring instructions by cache and
  pattern lookup, without a model call.
- **CLSR** (ICML 2026) lets LLM agents evolve compact symbolic reasoning languages, reporting 3–6× fewer generated
  tokens than chain of thought.
- **Verifiable Semantics for A2A** certifies terms behaviourally and recertifies them on drift.
- Invention methods (TRIZ, Synectics, morphological analysis), design structure matrices, memory palaces and
  anchoring each cover one part.

Each of these optimises one axis: size, structure or term meaning. A3 and A3b measure the axis they leave open: whether
every copy of the shared state stays true, and what it costs to make it true again. **What is new is the combination in
one executable language:**

- human-composable spatial programs, with the same operators on any host;
- consent and laws checked by the compiler;
- integrity and in-place healing inside the protocol;
- a cross-domain engine that chooses where to land and predicts the gain, tested against blind and weighted
  alternatives;
- an input layer that emits whole components.

We are not aware of a system that joins these.

## 11. Purpose and responsible use

RSOS grew from one seed: healing, transforming, signalling and evolving. It integrates the whole of human
experience, including its shadow, so that what is integrated can be transformed rather than denied. Because its seed
is healing, RSOS is used with consent and for the good of the person or system it works with, never to harm or
coerce. The design carries this: operations on people need their consent, harm checks are compiled into the
language, and the engine admits only changes that are measurable, new and of good intention (`RESPONSIBLE_USE.md`). RSOS is research software, not a medical device. No clinical, forensic or
financial claim is made before validated trials in that domain.

## 12. Research programme

The operators are defined independently of any domain. The programme (`whitepaper/RESEARCH_PROGRAMME.md`) tests this
in 24 domains, each with a first measurable test and its safeguards. They range from AI agent systems, decision-making
and sport to finance reconciliation, defensive cybersecurity, socio-technical safety and, with clinical partners and
ethics approval, computational psychiatry and neuroscience. The method is the same everywhere: bind the host,
pre-register, use the strongest baseline, report every failure, replicate independently.

## 13. Limits

- **One model family.** All agents are Haiku-class models from one provider, run at CLI-default temperature. The
  cross-family test needs third-party keys and is open.
- **Small samples.** 8–16 tasks per arm. The integrity and token differences are large against their CIs; success
  differences of one or two tasks are not established.
- **One task family.** The host is structured state editing; free-text collaboration is untested.
- **Re-implemented competitors.** D and E are rebuilt from public descriptions, not the original systems. Our lossless
  quantiser favours D.
- **Latent drift.** No agent reads another's copy for computation, so the cost of the anchor protocol's latent drift
  is not yet shown (A4).
- **Heal assumptions.** The zero-token heal assumes a second, untouched copy. With both copies corrupted, the heal
  costs 18.5 tokens per drift (offline).
- **Engine design calls.** A2 and A3b each used one design call, so the variance between calls is unmeasured.
- **Human evidence.** One person, the inventor. No effect on people has been shown.
- **Ledger instruments.** Three of five instruments tested (IMIP, CRI, ARC) did not track their claims and are being
  rebuilt.

## 14. Next tests (pre-registered before running)

- **A3c.** A shared deterministic predictor as the reference for the remaining prose, to test whether 5× is reachable
  with integrity unchanged. Projection only: about 280–370 tokens per task.
- **A4.** Agents compute from their own copies, to test whether latent drift turns into wrong results.
- **HT2.** The keyboard layer after the learning phase, on sealed novel tasks against plain text.
- **Cross-model replication** of A1–A3b on other model families.

## 15. Availability and citation

Code, specification, experiments, results and transcripts of the agent runs: Apache 2.0, at
github.com/r-a-elu-architecture/RSOS-Language (`./reproduce.sh`). The private development corpus is not released.
Cite as: R. A. Elu, *RSOS: an executable spatial-symbolic language for human–AI and AI–AI communication*, whitepaper
v2, 2026, Zenodo, https://doi.org/10.5281/zenodo.24304403 (all versions). Software: RSOS Language 0.2.0,
https://doi.org/10.5281/zenodo.24317658. Related: RSOS Multimodal Cue Framework v2.1.0,
https://doi.org/10.5281/zenodo.24301903.

References: Maio, *Slipstream: Semantic Quantization for Efficient Multi-Agent Coordination*, Zenodo
10.5281/zenodo.18063451 (2026). Benzing, *Agent Context Compression Protocol (ACCP)*, draft-benzing-accp-00 (2026).
Mackay, *Agent Action Compression Protocol (AACP)*, draft-mackay-aacp (2026). Pei, Huang, Wang, *When LLMs Develop
Languages: Symbolic Communication for Efficient Multi-Agent Reasoning*, ICML 2026, PMLR 306:97643–97678.
