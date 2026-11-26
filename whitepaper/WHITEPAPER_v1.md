# RSOS: an executable spatial-symbolic language for human–AI and AI–AI communication

**R. A. Elu** (r-a-elu-architecture) · Whitepaper v1 · approved by the author 17 November 2026 · DOI: 10.5281/zenodo.24304404 · Text: CC BY 4.0; code: Apache 2.0
Reference implementation: `rsoslang`, released as open source (Apache 2.0) alongside this paper. Status of every result is stated as measured; nothing
here is claimed beyond its evidence.

## Abstract

RSOS is a programming language whose programs are spatial and symbolic compositions (objects, places, flows,
beams, colours, dots, rooms, senses) and whose operators (heal, beam, contain, compress, inherit, transplant,
re-host, fuse, pierce, route by state, …) act on any host: a person, a team, an AI agent, an organisation or a
physical system. It was composed visually by its author over 2025–2026 and is serialised here as a compiled
language with 108 statements covering a register of 107 operator rows, a governance layer (consent, standing
consent in networks with laws, a seven-virtue Spine), a runtime, a two-way painting interface and a
communication layer for compressed, self-healing messages between parties. This paper describes the language,
the combination it introduces, and the pre-registered results so far: what runs on real code, what has only been
shown in simulation, and what failed. The first real-host test (AI agents against strong baselines) is
pre-registered and starts now.

## 1. The problem

People and AI systems exchange meaning through long text. Agents exchange JSON or natural language, re-send state
when it diverges, and have no shared way to notice that a word has silently changed meaning. Methods for
cross-domain invention (TRIZ, Synectics, morphological analysis) stop at ideas and work for people only.
Mental-model methods (memory palaces, anchoring) store content but are not executable. No single system lets a
person and an AI write the same program, run it on different hosts, and check that the meaning arrived intact.

## 2. The language

- **Components.** Every symbol is a component with properties, functions, processes, interfaces, levels, a host
  binding, a colour state and a position.
- **Operators** act on components; the **grammar** is spatial and sequential: the order of objects in a scene,
  paths, regions from the centre, depth and layers. The sequence is the program.
- **Hosts decide behaviour.** The same bundle behaves differently on a body, a person, a team, an agent or a
  planet; the compiler checks host compatibility.
- **Mental-model construction.** Cognition is built as an architecture: a house (the whole), rooms (states such as
  the view from above), objects (models run in that state), each part of an object carrying one model (a
  perspective plus a composition of components). The same house can hold external systems, so one architecture
  serves human cognition and AI workflows.
- **Painting interface.** Programs compile to paintings and paintings back to programs (`docs/editor.html`).

Specification: `spec/LANGUAGE.md`, `spec/REFERENCE.md`, `spec/SEMANTICS.md`.

## 3. Governance inside the language

Person-facing operations require consent (compiler error E018). Standing consent is valid only inside a declared
network with members and laws (`CONSENT host … SCOPE standing IN net` + `NETWORK … MEMBERS … LAWS …`, error
E021 otherwise). The cue framework's Spine (seven virtues) blocks predicted harm (E019). Governance is checked at
compile time, not appended as policy.

## 4. The communication layer

- **Palace.** Parties share a book of meanings; a message is a short sequence of anchors into it.
- **Green dot.** Each message carries a check of the book version, so a silent change of meaning (drift) is
  detected instead of misread.
- **White Dragon heal.** On drift, only the changed part is repaired, not the whole state re-sent.
- **Evolve-healing.** A repair keeps the better of two versions, decided by the White Dragon filter: measurable,
  new, good intention. Links between palaces are healed as well as books.

## 5. The White Dragon engine

A cross-domain creativity module over **spheres**. A sphere is a graph node with spatial extent: a surface, an
interior and a core. Landings have a position and a depth, and spheres can nest. Golden light finds paths between a
sphere and domain libraries by shared relations; a green particle lands on the shared relation and creates a
child sphere; the white light keeps only child spheres that are measurable, new and of good intention; child spheres
improve their parent and root spheres (cybernetic feedback). The knowing form (operator `TRANSPLANT … FROM … DEPTH …
ORDER … GAIN …`) selects a host part (a sphere), its best cross-domain equivalent, the depth and the order; the ordered
landings form a 3D connection map that is the build plan.

## 6. A self-measuring lineage

The language's own development is recorded as a ledger of 292 nodes in six epochs, each node with glyph, function,
command, echo and behaviour, plus 70 named instruments (43 tier metrics, 27 echo metrics). Read as executable
components, the instruments are themselves spheres of the White Dragon (48 metric spheres, 39 distinct relation signatures).

## 7. Results

Every experiment was pre-registered and committed before it ran; results carry a hash; `./reproduce.sh` reruns
the released ones. Experiments on the 2025 ledger are reported here, and their data stays private in v1. Failures are reported with the successes.

**On real code (the compiler and protocol themselves)**

| Test | Result |
|---|---|
| C1 palace messages | 14-token messages decoded exactly 280/280; drift detected 366/366; heal at 0.36× the cost of a resend |
| T7 structure vs names | meaning carried by structure 98.3% vs by names 3.3%; **graceful under 10% relation noise: 47.5% (failed)** |
| T8 one program, two runtimes | a person's session (5 steps, 37 events) and an agent (accuracy 0.488 → 0.762) from the same program |
| U1b standing consent (on the private ledger; data not released in v1) | 0 blocked with network + laws; 66/66 refused without the visible member; 60/60 network triggers blocked without consent |

**In simulation (mechanisms shown; effect in the world not yet measured)**

| Test | Result |
|---|---|
| V1 sense keys | one rich sense channel opens the anchored state 0.90–0.92 vs a name key 0.18; green dot: 205 silent wrong opens → 0 |
| H1 predictive heal | failed first uses 9.2% → 4.9% (byte cost higher) |
| H2b where help is needed | host reporting net of help already on the way: 0.998 working share vs 0.909 random |
| H3c evolve-healing by filter | quality −0.19 (restore) → +0.67; harmful copies 4.95% → 0.60%; captures 50% of an oracle's gain |
| E1 White Dragon growth | 48 → 243 → 1,667 → 9,268 filtered child spheres; deficit targeting 2.5× |
| F1b feedback | child spheres improve root spheres (deficit −0.22); **entry reinforcement adds only +0.02 (failed)** |

**Failed or negative, kept on record:** R-003 move + pierce interaction (negative in 40/40 worlds); R-004 four
placement rules; T5 sign change across real hosts; several thresholds in S1, E1, V1, H1, U1. Full list:
`results/BUILD_REPORT.md` and each `experiments/*_REPORT.md`.

## 8. Pre-registered next test (A1, A2)

AI agents share a multi-step task and communicate either in the palace language or through three strong
baselines (plain JSON, structured outputs, summaries + retrieval). Measures: tokens per completed task, success,
injected drift caught, recovery cost, truncation tolerance. Predictions fixed in advance: palace ≤ 0.5× the tokens
of JSON at equal success; ≥ 95% drift caught; recovery ≤ 0.5× resend. A2 tests the knowing White Dragon against
blind and weighted transplants, and whether its order beats a shuffled order. Whitepaper v2 will report both.

## 9. Related work and what is new

Compact agent messaging is an active field: Slipstream (shared concept references, ~82% fewer tokens), ACCP (delta
encoding), CLSR (ICML 2026; agents evolve compact symbol systems, 3–6× fewer tokens), Verifiable Semantics for A2A
(behavioural certification of terms, drift recertification). Invention methods (TRIZ, Synectics, morphological
analysis), design structure matrices, memory palaces and anchoring each cover one part. **What is new is the
combination in one executable language:** human-composable spatial programs; the same operators on any host;
consent and laws checked by the compiler; drift detection and healing that also improves content; a creativity
engine that grows new components where measurement shows a lack and lands them in a set order; and a
self-measuring lineage of the language's own development. We are not aware of a system that joins these.

## 10. Limits

Most mechanism results are simulations built on assumptions stated in each pre-registration. No effect on people
has been measured. Three of the five ledger instruments tested (IMIP, CRI, ARC) did not track what they claim and
are being rebuilt. The cross-model test (different AI families) is pending.

## 11. Availability and citation

Code, specification, experiments and results: Apache 2.0. This text: CC BY 4.0. The private development corpus is not released.
Cite as: R. A. Elu, *RSOS: an executable spatial-symbolic language for human–AI and AI–AI communication*,
whitepaper v1, 2026, Zenodo, https://doi.org/10.5281/zenodo.24304404. See `CITATION.cff`.
Related: RSOS Multimodal Cue Framework v2.1.0, https://doi.org/10.5281/zenodo.24301903.
