---
license: apache-2.0
pretty_name: RSOS pre-registered multi-agent experiments
tags:
  - multi-agent
  - llm-agents
  - agent-communication
  - shared-state
  - mcp
  - pre-registered
  - negative-results
---

# RSOS pre-registered multi-agent experiments (A1–A5)

Results, transcripts, pre-registrations and reports of the RSOS experiments on real LLM agents. Every experiment was
pre-registered before it ran; every failed prediction is included.

**Headline (A5):** in a three-agent workflow that edits a shared 30-line state over 14 change requests with injected
drift, the RSOS State Runtime used **2.2–2.4 model calls per task instead of 42–43**, **0.27–0.35× the cost** of the
same agents run one model call per step (our per-step protocol, API prices), and was **32/32 exact**. Under drift where agents compute from
their own copies (A4), a Slipstream-style anchor protocol (our re-implementation, without the hash check and restore) got
0/16 tasks right. A7 (80 tasks, 14–224 steps, up to 300 keys): against one-call JSON Patch with the same hash check, RSOS blind was
80/80 exact vs 77/80, the planner shown no state value; cost per correct task 0.50–0.91×.

**Limits:** one model family, one task family, 16 tasks per set. The 10× cost target was missed. 51 pre-registered
predictions so far: 29 passed, 22 failed.

## Contents

| Path | What |
|---|---|
| `experiments/PREREGISTRATION_*.md` | the predictions, written before each run |
| `experiments/*_REPORT.md` | the reports, with every verdict |
| `results/*_results_*.jsonl` | one record per task and arm: success, accuracy, final state, drift events |
| `results/*_transcripts_*.jsonl` | every message between agents and runtime, with token counts |
| `results/*.json` | analyses; each carries a `results_sha256` you can recompute |

Two A3c coded transcripts are held back; their SHA-256 and text-free counts are in `results/a3c_withheld.json`, and
`experiments/a3c_edges_check.py` reproduces every A3c number from the counts.

## Reproduce

Code, analysis scripts and the one-hour replication guide (under $1):
[github.com/r-a-elu-architecture/RSOS-Language](https://github.com/r-a-elu-architecture/RSOS-Language)
(`REPLICATE.md`). Every analysis re-runs from these files with 0 model calls.

## Cite

R. A. Elu (2026), *RSOS whitepaper v2*, [doi:10.5281/zenodo.24320392](https://doi.org/10.5281/zenodo.24320392).
Software: [doi:10.5281/zenodo.24321030](https://doi.org/10.5281/zenodo.24321030).
