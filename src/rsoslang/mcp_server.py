"""MCP server for the RSOS Language: lets Claude or any MCP-capable assistant read, write and run RSOS programs.

Run:  rsoslang mcp   (or rsoslang-mcp, or python -m rsoslang.mcp_server)        stdio transport
Install:  pip install rsoslang      No install:  uvx rsoslang mcp

Tools
  rsos_statements      the language: every statement with its signature and an example
  rsos_check           compile a program; errors and warnings (including the Spine's governance)
  rsos_compile         compile a program to its JSON IR (with its SHA-256)
  rsos_session         a person's practice session: RSX program + the cue framework's timeline summary
  rsos_paint_workflow  the 12-module support agent as a painting, with measured metrics
  rsos_apply_gestures  apply gestures (RSOS statements) to the support agent; measured before/after on held-out tickets
  rsos_paint_graph     paint an external agent graph (LangGraph-style JSON) and turn gestures into graph edits

  RSOS State Runtime (the model decides, the language executes; A4, A5):
  rsos_state_new       start a shared state; returns its id and green dot
  rsos_state_prompt    one prompt that turns ALL of a task's requests into RSOS operations (any model)
  rsos_state_apply     execute operations or a whole '#n' plan; the runtime computes every value
  rsos_state_sync      check an agent's copy against the green dot and heal drifted lines (0 model calls)
  rsos_state_get       the agreed state and its green dot
"""

import json

try:                                   # MCP Python SDK 2.x
    from mcp.server.mcpserver import MCPServer
except ImportError:                    # SDK 1.x: the same server under its earlier name
    try:
        from mcp.server.fastmcp import FastMCP as MCPServer
    except ImportError as e:
        raise SystemExit("rsoslang MCP server needs the MCP SDK: pip install mcp") from e

from . import compile_source
from .grammar import STATEMENTS, signature

server = MCPServer(name="rsos-language", version="0.3.1",
                   instructions="RSOS State Runtime: for work that edits a shared state over many steps, call rsos_state_new, "
                                "then rsos_state_prompt once for ALL requests, answer that prompt with operations, and "
                                "pass them to rsos_state_apply: the runtime computes every value. Use rsos_state_sync "
                                "to check and heal any agent's copy (0 model calls). RSOS Language: write programs as "
                                "scenes; use rsos_statements to learn it and rsos_check before running anything. "
                                "Person-facing programs need CONSENT.")
_DATA = {}


def _tickets():
    if "A" not in _DATA:
        from .agents.tickets import make_tickets
        _DATA["A"] = make_tickets(500, 2, typo_rate=0.3, unseen_rate=0.3)
    return _DATA["A"]


@server.tool(description="List every RSOS statement with its register links, signature and an example.")
def rsos_statements() -> str:
    return json.dumps({s.kw: {"family": s.family, "signature": signature(s), "example": s.doc}
                       for s in STATEMENTS.values()}, ensure_ascii=False)


@server.tool(description="Compile an RSOS program and report errors and warnings (governance included).")
def rsos_check(source: str) -> str:
    res = compile_source(source)
    return json.dumps({"ok": res.ok, "diagnostics": [d.to_dict() for d in res.diagnostics],
                       "operations": len(res.ir["ops"])}, ensure_ascii=False)


@server.tool(description="Compile an RSOS program to its JSON intermediate representation.")
def rsos_compile(source: str) -> str:
    res = compile_source(source)
    return json.dumps({"ok": res.ok, "sha256": res.digest(), "ir": res.ir}, ensure_ascii=False, default=str)


@server.tool(description="Compile a program with a person host into a practice session (RSX + timeline summary).")
def rsos_session(source: str) -> str:
    from .mind.session import compile_session
    res = compile_source(source)
    if not res.ok:
        return json.dumps({"ok": False, "errors": [str(d) for d in res.errors]})
    s = compile_session(res.ir)
    return json.dumps({"ok": True, "rsx": s["rsx"], "steps": len(s["steps"]), "skipped": s["skipped"],
                       "timeline_events": len(s["timeline"]["events"]),
                       "duration_s": s["timeline"].get("duration_ms", 0) / 1000, "footer": s["footer"]},
                      ensure_ascii=False)


@server.tool(description="The 12-module support agent as a painting, with metrics measured on held-out tickets.")
def rsos_paint_workflow() -> str:
    from .agents.workflow import build
    from .painting.scene import encode
    wf = build()
    return json.dumps(encode(wf, wf.evaluate(_tickets(), 2)), ensure_ascii=False)


@server.tool(description="Apply gestures (RSOS statements such as 'PIERCE spell_corrector THROUGH classify.brain') "
                         "to the support agent and measure the effect on 500 held-out tickets.")
def rsos_apply_gestures(gestures: str) -> str:
    from .agents.workflow import build
    from .painting.scene import apply
    base = build()
    try:
        wf, changes = apply(base, gestures if gestures.endswith("\n") else gestures + "\n")
    except ValueError as e:
        return json.dumps({"ok": False, "error": str(e)})
    keys = ("accuracy", "crashed", "cost_per_ticket", "score")
    b, a = base.evaluate(_tickets(), 2), wf.evaluate(_tickets(), 2)
    return json.dumps({"ok": True, "changes": changes, "before": {k: b[k] for k in keys},
                       "after": {k: a[k] for k in keys}})


@server.tool(description="Paint an external agent graph (LangGraph-style JSON: nodes with id, edges with source/target) "
                         "and optionally turn gestures [[op, guest, node, place], ...] into graph edits.")
def rsos_paint_graph(graph_json: str, gestures_json: str = "[]") -> str:
    from .painting.graphs import read_graph, patch
    scene = read_graph(json.loads(graph_json))
    edits = patch(scene, [tuple(g) for g in json.loads(gestures_json)])
    return json.dumps({"scene": scene, "edits": edits})


# ---- RSOS State Runtime (A4, A5) -------------------------------------------------------------------------------
_LEDGERS = {}


def _ledger(state_id):
    if state_id not in _LEDGERS:
        raise ValueError(f"unknown state id {state_id!r}; call rsos_state_new first")
    return _LEDGERS[state_id]


@server.tool(description="Start a shared state (JSON object of dotted keys to values). Returns its id and green dot.")
def rsos_state_new(state_json: str) -> str:
    from .core.state import Ledger
    led = Ledger(json.loads(state_json))
    sid = f"s{len(_LEDGERS) + 1}"
    _LEDGERS[sid] = led
    return json.dumps({"id": sid, "dot": led.dot, "keys": len(led.state)})


@server.tool(description="One prompt for a whole task: give a JSON list of change requests; send the returned system and "
                         "user text to any model; pass its reply to rsos_state_apply. One call instead of one per step.")
def rsos_state_prompt(state_id: str, requests_json: str) -> str:
    from .core.state import plan_prompt
    return json.dumps(plan_prompt(json.loads(requests_json), _ledger(state_id).state), ensure_ascii=False)


@server.tool(description="Execute RSOS operations, or a whole plan with '#n' step headers, on the shared state. The "
                         "runtime reads and computes every value; failed steps come back with a reason and change nothing.")
def rsos_state_apply(state_id: str, operations: str) -> str:
    from .core.state import parse_plan
    led = _ledger(state_id)
    plan = parse_plan(operations)
    out = led.apply_plan(plan) if plan else led.apply(operations)
    return json.dumps(out, ensure_ascii=False)


@server.tool(description="Check an agent's copy (JSON object) against the agreed state's green dot and heal every drifted "
                         "line, with zero model calls. Returns the healed copy and the list of drifted keys.")
def rsos_state_sync(state_id: str, replica_json: str) -> str:
    return json.dumps(_ledger(state_id).sync(json.loads(replica_json)), ensure_ascii=False)


@server.tool(description="The agreed shared state and its green dot.")
def rsos_state_get(state_id: str) -> str:
    return _ledger(state_id).to_json()


def main():
    server.run("stdio")


if __name__ == "__main__":
    main()
