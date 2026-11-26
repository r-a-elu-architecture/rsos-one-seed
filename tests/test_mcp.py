"""The MCP server lists and runs its tools (in-process)."""
import asyncio
import json

import pytest

mcp = pytest.importorskip("mcp.server.mcpserver")


def test_tools_listed_and_callable():
    from rsoslang.mcp_server import server

    async def go():
        tools = {t.name for t in await server.list_tools()}
        r = await server.call_tool("rsos_check", {"source": "LANGUAGE RSOS 0.2\nWORLD w\nOBJECT a\n"})
        return tools, r
    tools, r = asyncio.run(go())
    assert {"rsos_check", "rsos_compile", "rsos_session", "rsos_apply_gestures", "rsos_paint_graph"} <= tools
    text = r.content[0].text
    assert json.loads(text)["ok"] is True


def test_state_runtime_tools_end_to_end():
    from rsoslang.mcp_server import server

    async def go():
        call = lambda n, a: server.call_tool(n, a)           # noqa: E731
        sid = json.loads((await call("rsos_state_new", {"state_json": json.dumps({"auth.timeout_ms": "700", "auth.owner": "chen"})})).content[0].text)["id"]
        p = json.loads((await call("rsos_state_prompt", {"state_id": sid, "requests_json": json.dumps(["raise auth timeout by 100"])})).content[0].text)
        a = json.loads((await call("rsos_state_apply", {"state_id": sid, "operations": "#0\nINHERIT auth.timeout_ms auth.timeout_ms +100\n"})).content[0].text)
        h = json.loads((await call("rsos_state_sync", {"state_id": sid, "replica_json": json.dumps({"auth.timeout_ms": "1", "auth.owner": "chen"})})).content[0].text)
        return p, a, h
    p, a, h = asyncio.run(go())
    assert "#0" in p["user"] and a["failed"] == [] and h["healed"] == ["auth.timeout_ms"] and h["state"]["auth.timeout_ms"] == "800"
