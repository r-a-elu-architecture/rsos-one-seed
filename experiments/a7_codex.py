"""A8 backend: OpenAI models through the Codex CLI on the owner's ChatGPT plan (`codex exec`), for every arm alike.

The counterpart of `claude -p` on the Claude plan (A5-A8). Used by a7_run.py when A7_BACKEND=codex. Environment:
  A7_CODEX_MODEL   optional model id (passed as -m); recorded in every call
  A7_CODEX_BIN     optional path to the codex executable (default: found on PATH)
Each call: `codex exec --json --skip-git-repo-check --sandbox read-only -C <empty temp dir> -` with the prompt on stdin;
the system text is placed before the task text, as the CLI has no separate system field. The answer is the last agent
message. Token counts come from the CLI's usage events. **Any tool use** (a shell command, file change, web search or
MCP call) is recorded per call as `tools`; the analysis reports such tasks separately (amendment 9), because the
planner must answer from the prompt alone. Standard library only.
"""

import json
import os
import shutil
import subprocess
import tempfile
import time

MODEL = os.environ.get("A7_CODEX_MODEL", "")
BIN = os.environ.get("A7_CODEX_BIN") or shutil.which("codex") or "codex"
TOOL_ITEMS = {"command_execution", "file_change", "mcp_tool_call", "web_search", "patch_apply", "exec_command"}


def _num(u, *keys):
    for k in keys:
        if isinstance(u.get(k), (int, float)):
            return int(u[k])
    return 0


def parse(stdout):
    """Last agent message, summed usage, tool items, model (if reported) from the CLI's JSON lines."""
    text, tools, model = "", [], None
    usage = {"in": 0, "cache_r": 0, "out": 0, "think": 0}
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        item = ev.get("item") or ev.get("msg") or {}
        kind = item.get("type") or item.get("item_type") or ""
        if ev.get("type") in ("item.completed", "item.updated") or item:
            if kind in ("agent_message", "assistant_message") and isinstance(item.get("text"), str):
                text = item["text"]
            elif kind in TOOL_ITEMS:
                tools.append(kind)
        u = ev.get("usage") or (ev.get("info") or {}).get("last_token_usage")
        if isinstance(u, dict) and ev.get("type") in ("turn.completed", "token_count", None):
            usage["in"] += _num(u, "input_tokens", "prompt_tokens")
            usage["cache_r"] += _num(u, "cached_input_tokens")
            usage["out"] += _num(u, "output_tokens", "completion_tokens")
            usage["think"] += _num(u, "reasoning_output_tokens", "reasoning_tokens")
        model = ev.get("model") or model
    return text, usage, tools, model


def raw_call(system, prompt, timeout=900):
    cmd = [BIN, "exec", "--json", "--skip-git-repo-check", "--sandbox", "read-only"]
    if MODEL:
        cmd += ["-m", MODEL]
    body = ("Answer from this message alone. Do not run commands, read files or search; reply with the answer only.\n\n"
            "SYSTEM:\n" + system + "\n\nTASK:\n" + prompt)
    t0 = time.time()
    with tempfile.TemporaryDirectory(prefix="rsos_a8_") as empty:
        p = subprocess.run(cmd + ["-C", empty, "-"], input=body, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout, cwd=empty)
    text, u, tools, model = parse(p.stdout)
    if p.returncode != 0 and not text:
        raise RuntimeError(f"codex exit {p.returncode}: {(p.stderr or p.stdout)[-300:]}")
    rec = {"in": u["in"] - u["cache_r"], "cache_w": 0, "cache_w5m": 0, "cache_w1h": 0, "cache_r": u["cache_r"],
           "out": u["out"], "think": u["think"], "sec": time.time() - t0, "api_ms": None, "turns": 1,
           "cost": 0.0, "model": model or MODEL or "codex-default", "tools": tools}
    return text, None, rec


def llm(system, prompt, schema=None, log=None, model=None):
    err = ""
    for attempt in range(4):
        try:
            text, so, rec = raw_call(system, prompt)
            if log is not None:
                log.append({"kind": "llm", "system": system[:40], "prompt": prompt, "text": text,
                            "structured": so, **rec})
            return text, so, rec
        except Exception as e:  # noqa: BLE001  usage limits and transient errors: wait, then retry
            err = str(e)[:300]
            time.sleep(30 * (attempt + 1))
    raise RuntimeError("codex call failed: " + err)


def install():
    import a5_llm as L
    L.llm = llm
    L.raw_call = lambda system, prompt, model=None, legacy=False, timeout=900: raw_call(system, prompt, timeout)
