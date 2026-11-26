# RSOS Language

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24304403.svg)](https://doi.org/10.5281/zenodo.24304403) [![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE) [![tests](https://github.com/r-a-elu-architecture/RSOS-Language/actions/workflows/tests.yml/badge.svg)](https://github.com/r-a-elu-architecture/RSOS-Language/actions/workflows/tests.yml)

**Exact shared state for AI agents.** The model names what should change; a deterministic runtime computes every
value, checks every agent's copy against a 12-digit state digest and repairs drift with zero model calls. The planner
never sees a state value. Software: [doi:10.5281/zenodo.24359268](https://doi.org/10.5281/zenodo.24359268) (v0.4.0, Core 1.0;
all versions [doi:10.5281/zenodo.24317657](https://doi.org/10.5281/zenodo.24317657)). Whitepaper:
[doi:10.5281/zenodo.24304403](https://doi.org/10.5281/zenodo.24304403). Code: Apache 2.0.

## Blind planning: the model names keys, the runtime computes values

```
reassign_where(field=owner, from=bruno, to=chen)          # Core syntax
REHOST owner bruno chen                                   # RSOS syntax: same IR, same digest
```

The planner writes each change request as operations over key names; the runtime finds every matching key, does the
arithmetic, applies caps and conditions, and executes each step atomically.

| Measured (pre-registered) | RSOS blind planning | One-call JSON Patch (strongest pattern we could build) |
|---|---|---|
| A7: 80 tasks, 14–224 steps, up to 300 keys (Claude Haiku) | **80/80 exact**, 0 wrong steps in about 5,800 | 77/80; all 8 failed steps were values computed from changed state |
| A8: six models from Anthropic, Google, Mistral and OpenAI | **256/256 exact** | failures on one request type: "everything owned by X is now owned by Y" |
| SC1: a robot scene shared by six robots (Mistral Large 4, Gemini 3.8 Flash) | **32/32 exact** | 29/32; failed at **two of five hand-overs named before the run** |
| SC2: FLOW, an operation predicted before it existed; tasks from a public randomness beacon (Mistral Large 4) | **16/16 exact**; 14/16 on the control | failed **14.8%** of FLOW requests (predicted ≥ 5%) |
| Cost per correct task at 300 keys | **0.45–0.61×** (USD on Mistral; tokens on Gemini, GPT) and 0.50–0.54× (Claude) | 1× |
| Against one model call per step (A5) | 2.2–2.4 calls instead of 42–43 | |

**Predicted in public, then confirmed.** Before running three model families we had never tested, we published where
JSON Patch would break: task 712 or 702, step 35 (G9, commit `00e5121`, 18 Nov 22:26 UTC; G10, `edcd42e`, 19 Nov 02:50
UTC). Gemini 3.8 Flash, Mistral Large 4 and GPT-6.2 Sol each failed at that step; RSOS blind stayed exact on all of
them. Report: [`experiments/A8_FAMILIES_REPORT.md`](experiments/A8_FAMILIES_REPORT.md).

**Then in a world no model had seen.** SC1, a robot scene (50 objects shared by six robots), was published with five
named hand-over steps at 05:43 UTC on 19 Nov, before any model call. Mistral Large 4's JSON Patch failed at two of them
(task 913, steps 53 and 49); Gemini 3.8 Flash's failed elsewhere (906/45, published as a miss). RSOS blind: 32/32.
Report: [`experiments/SC1_REPORT.md`](experiments/SC1_REPORT.md).

**Limits.** One task family (configuration-style key–value state), 16 tasks per cell; JSON Patch is strong, so the
exactness gap is small and concentrated in one request type; the tool-calling and code-writing rivals are not yet run;
26 of 76 predictions failed and are published, including the first two RSOS blind task failures (SC2 control). Next tests, with predictions fixed in advance:
**[NEXT_TESTS.md](NEXT_TESTS.md)**.

**Try to break it.** Score any framework on the same tasks with **[RSOS-StateBench](bench/)** (plain JSONL and a
scorer), or re-run every analysis from the recorded transcripts with zero model calls ([REPLICATE.md](REPLICATE.md)).

```bash
pip install rsoslang                             # 0.4.0: RSOS Core 1.0 and the State Runtime
claude mcp add rsos -- rsoslang mcp              # or with no install: claude mcp add rsos -- uvx rsoslang mcp
python experiments/a5_runtime_equivalence.py     # from a clone: this runtime replays every measured plan, 32/32 match
```

**RSOS Core 1.0** is the specification behind this: eight operations, a JSON IR with a schema and a digest, stable
error codes, conformance tests and an operator registry ([`spec/core/STATE_OPS.md`](spec/core/STATE_OPS.md),
[`registry/operators.json`](registry/operators.json)). An operation enters Core only once it is tested and backed by
an experiment.

**MCP:** in the [official MCP Registry](https://registry.modelcontextprotocol.io/v0/servers?search=io.github.r-a-elu-architecture/rsos)
as `io.github.r-a-elu-architecture/rsos`. Works in any MCP client over stdio (Claude Code, Claude Desktop, Cursor and
others). [State Runtime guide](STATE.md), [website](https://r-a-elu-architecture.github.io/RSOS-Language/),
[all results, failures included](https://r-a-elu-architecture.github.io/RSOS-Language/results.html).

## The language

**A spatial-symbolic programming language for humans and AI.** You write a program the way you think it: objects in
a scene, placed, touched, pierced, entered, coloured, connected by lines, kept in the rooms of a house. The same
program runs in two places:
- in a **machine**: an AI agent workflow, a simulation;
- in a **person**: a practised mental model, delivered as a timed session of images, words, sounds, scents and
  vibration codes.

State programs written in the spatial syntax compile to the same Core IR as the text above. What is measured so far is
the runtime and the planning protocol; the first grounded robot scene (SC1: 50 objects shared by six robots, 300 keys) ran on two
models after its predictions were published: RSOS blind 32/32 exact, JSON Patch failed at two named steps, 0.52–0.61×
the tokens per correct task. With 0 model calls: the RSOS program plus state digest is 0.49× the bytes and 0.22× the
tokens of a JSON Patch delta, and 0.0054× a full scene-graph sync; it is larger on conditional steps (1.20×)
([SC1_REPORT.md](experiments/SC1_REPORT.md)).

**[Open the editor](docs/editor.html).** A real 12-module support agent, painted. Put a guest at the head, heart,
brain or beside a module, and see the measured effect.

**All results** (pre-registered, real LLM agents, every failure reported; 76 predictions so far, 50 passed, 26
failed): [results page](https://r-a-elu-architecture.github.io/RSOS-Language/results.html). Newest first: **A8** (six models from four companies;
a stronger JSON Patch; G9 and G10 hit), **A7b** (long tasks and large states), **A7a** (blind planning vs one-call JSON Patch, above), **A5** (one plan vs one call per step), **A4** (hidden drift becomes
wrong answers for an anchor protocol without a hash check: 0/16), **A3c** (0.141× the channel tokens of a
Slipstream-style anchor protocol at zero model calls). Whitepaper v2 ([doi:10.5281/zenodo.24320392](https://doi.org/10.5281/zenodo.24320392),
17 Nov) covers A1–A3b and HT1; A3c–A8 are in `experiments/` and will be in the next version.

**First real-host test (A1, 17 Nov 2026, pre-registered):** three LLM agents (planner, worker, checker) on 8 tasks. The RSOS palace protocol used about 7× fewer channel tokens than JSON with full state (2,563 vs 17,311), finished 7/8 tasks exactly correct (JSON 5/8), and caught and healed 24/24 injected drifts with 0 model calls (38 tokens per repair). Summaries + retrieval: 0/8 correct, 24/24 drifts kept. One model family, 8 tasks. Report: [`experiments/A1_REPORT.md`](experiments/A1_REPORT.md).

## Purpose

RSOS grew from one seed: healing, transforming, signalling and evolving. It integrates the whole of human
experience, including its shadow, so that what is integrated can be transformed rather than denied. Because its seed
is healing, RSOS is used with consent and for the good of the person or system it works with, never to harm or
coerce. See [`RESPONSIBLE_USE.md`](RESPONSIBLE_USE.md),
[`GOVERNANCE.md`](GOVERNANCE.md), [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`TRADEMARKS.md`](TRADEMARKS.md).

## What makes it different

- **Where you place an operator decides what it does.** The same spell corrector placed at a module's head, heart,
  brain or beside it gives four different results, measured on held-out data.
- **Meanings in three tiers.**
  - a fixed core, shared by everyone;
  - declared variations, scoped to a person, host, world or state;
  - meanings left open on purpose, found by search.

  Nothing changes silently.
- **The host decides.** Every operation runs on a declared host with its own channels and states. A cue on a channel
  the host does not have is an error.
- **Safety is in the compiler.** Person-facing operations need consent and pass a constitution of seven checks;
  return to baseline is always available.
- **Every result is reproducible.** Pre-registered experiments, seeds, result hashes; negatives published with
  positives.

## Quick start

```bash
pip install -e .
python -m rsoslang check examples/robot_head.rsl
python -m rsoslang ir examples/sol_remote.rsl
RSOS_CUE_FRAMEWORK=/path/to/RSOS-Multimodal-Cue-Framework python -m rsoslang session examples/healing.rsl
./reproduce.sh
```

## Use it from Claude or any MCP assistant

```bash
pip install rsoslang
claude mcp add rsos -- rsoslang mcp              # or: claude mcp add rsos -- uvx rsoslang mcp
```

Any other MCP client: a stdio server with command `rsoslang` and argument `mcp`
(`{"mcpServers": {"rsos": {"command": "rsoslang", "args": ["mcp"]}}}`).

**State Runtime tools:** `rsos_state_new`, `rsos_state_prompt`, `rsos_state_apply`, `rsos_state_sync`,
`rsos_state_get` (see [STATE.md](STATE.md)). **Language tools:** `rsos_statements`, `rsos_check`, `rsos_compile`,
`rsos_session`, `rsos_paint_workflow`, `rsos_apply_gestures`, `rsos_paint_graph`. Person-facing sessions need the
cue framework (`RSOS_CUE_FRAMEWORK=/path/to/RSOS-Multimodal-Cue-Framework`).

## Results

Every pre-registered test, the ones that failed included, on the
[results page](https://r-a-elu-architecture.github.io/RSOS-Language/results.html); the failure map is
[`experiments/FAILURES_MAP.md`](experiments/FAILURES_MAP.md); the next tests are in [NEXT_TESTS.md](NEXT_TESTS.md).
Earlier simulation and code results: [`results/BUILD_REPORT.md`](results/BUILD_REPORT.md).

## Licence

Apache 2.0. Research and development software; not a medical device.

<!-- mcp-name: io.github.r-a-elu-architecture/rsos -->
