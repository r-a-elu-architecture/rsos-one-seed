# RSOS State Runtime: drop it into your agents

**For multi-agent workflows that edit shared state** (configs, plans, tickets, records, models that several agents
read and write). The model decides what should change; the RSOS runtime executes it, checks every copy and heals
drift. Measured on real LLM agents (A4, A5; pre-registered, every failure reported):

| | Same agents, one call per step (our per-step protocol) | RSOS (assembly line) |
|---|---|---|
| Model calls for a 14-step task | 42–43 | **2.2–2.4** |
| Cost per task (API prices) | 1× | **0.27–0.35× (2.8–3.7× cheaper)** |
| Time per task | ~100 s | **12 s** |
| Tasks fully correct | 31/32 | **32/32** |
| Injected drifts healed without a model call | 96/96 | **96/96** |

And when agents compute from their own copies, a Slipstream-style anchor protocol (our re-implementation) got
**0 of 16** tasks right, with 93 of 96 wrong values traced to silent drift; the RSOS integrity protocols got 15–16 of
16 (A4). These numbers come from the experiment harness (`experiments/a5_*.py`); this runtime is the same operation
set and integrity layer, packaged. Verify them yourself: [REPLICATE.md](REPLICATE.md).

## In 60 seconds (Python)

```bash
pip install rsoslang        # or, from a clone of this repository: pip install -e .
```

```python
from rsoslang.state import Ledger, plan_prompt, parse_plan

led = Ledger({"auth.timeout_ms": "700", "auth.retries": "3", "search.retries": "6"})
p = plan_prompt(["Raise auth timeout by 100", "Set auth retries to auth plus search, at most 8"], led.state)
reply = your_model(p["system"], p["user"])          # one call for the whole task, any model
out = led.apply_plan(parse_plan(reply))             # the runtime computes every value; failures come back with a reason
healed = led.sync(worker_copy)                      # any agent's copy: drift restored, 0 model calls
```

## As an MCP tool (Claude Code, Claude Desktop, any MCP client)

```bash
pip install rsoslang
claude mcp add rsos -- rsoslang mcp
```

Official MCP Registry: [`io.github.r-a-elu-architecture/rsos`](https://registry.modelcontextprotocol.io/v0/servers?search=io.github.r-a-elu-architecture/rsos) (0.3.1). Verified on Windows 11 (18 Nov 2026): `pip install
rsoslang`, `claude mcp add` → Connected; `uvx rsoslang mcp` starts with no install.

Claude Desktop or any other MCP client: a stdio server with command `rsoslang` and argument `mcp` (or command `uvx`,
arguments `rsoslang mcp`: no install step). From a clone without installing: `claude mcp add rsos -- python -m rsoslang.mcp_server`
run from the repository with `PYTHONPATH=src`.

```text
Try it: "Start an RSOS state with auth.timeout_ms=700 and auth.retries=3, then apply: raise the timeout by 100 and set
retries to 5. Show me the green dot."
```

Tools: `rsos_state_new`, `rsos_state_prompt` (one prompt for all requests), `rsos_state_apply` (execute a plan),
`rsos_state_sync` (heal an agent's copy, 0 model calls), `rsos_state_get`.

## In a LangGraph workflow

[`examples/langgraph_state.py`](examples/langgraph_state.py): three nodes (planner, runtime, agents) replace a
model call per step with one call for the whole task; every agent's copy is synced to the green dot with zero model
calls. The nodes are plain functions, so the example also runs without LangGraph installed.

## The operations

`SET k v` · `DEL k` · `INHERIT d s [+n] [CAP m]` · `FUSE d a b [CAP m]` · `SCALE k f [CAP m]` ·
`ROUTE s = x : d v1 | v2` · `REHOST field a b`. Keys are dotted names; the model names keys, the runtime reads and
computes every value. `SET k other.key` copies the value of `other.key`, and is an error if that key does not exist;
to set text that contains a dot, quote it: `SET k "a.b"`. `SCALE` must produce a whole number. That is why a whole task fits in one call: the operations do not depend on the state, so steps
no longer wait for each other's model round trips.

## Limits (stated, not hidden)

Six models from four companies so far (Claude Haiku, Sonnet, Opus; Mistral Large 4; Gemini 3.8 Flash; GPT-6.2 Sol;
A7, A8), one task family (structured state editing), 16 tasks per cell. 10× was the target and was not reached; the
measured cost per correct task at 300 keys is 0.45–0.61× of one-call JSON Patch. A tool-calling baseline and real
workflows are what we test next: run it on yours and tell us.