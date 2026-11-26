"""A5 LLM call: the A1 harness call (`claude -p`) with the Phase 0 cache fix. PREREGISTRATION_A5.md.

Diagnosis (results/a5_cache_diagnosis.json): every A1-A4 call ran inside the remote session's environment, so the CLI
appended ~1,350 tokens of session context (environment, scratchpad, proxy, attribution and account reminders) after
the agent's system prompt, and on a subscription the CLI writes the cache with the 1-hour TTL (2x input). The agent's
own static prefix (~60-150 tokens) is below the 512-token minimum cacheable prefix, so the whole prompt was written to
cache on every call and never read.

Fix (identical for every A5 arm): run the CLI in a clean environment (only PATH, HOME, proxy and CA variables), force
the 5-minute TTL, no slash commands or MCP servers, and put the static part of each prompt first (system prompt, then
the static instructions) with the volatile part (request, state) last.
"""

import json
import os
import subprocess
import time

MODEL = os.environ.get("A5_MODEL", "claude-haiku-5-5")
KEEP = ("PATH", "HOME", "HTTPS_PROXY", "HTTP_PROXY", "https_proxy", "http_proxy", "NO_PROXY", "no_proxy",
        "SSL_CERT_FILE", "NODE_EXTRA_CA_CERTS", "REQUESTS_CA_BUNDLE", "ANTHROPIC_BASE_URL")


def clean_env():
    env = {k: os.environ[k] for k in KEEP if k in os.environ}
    env["FORCE_PROMPT_CACHING_5M"] = "1"
    return env


def raw_call(system, prompt, model=None, legacy=False, timeout=180):
    """One CLI call. legacy=True reproduces the A1-A4 call (inherited environment, default TTL)."""
    cmd = ["claude", "-p", "--output-format", "json", "--model", model or MODEL, "--system-prompt", system,
           "--tools", "", "--no-session-persistence"]
    if not legacy:
        cmd += ["--disable-slash-commands", "--strict-mcp-config"]
    env = None if legacy else clean_env()
    t0 = time.time()
    p = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=timeout, cwd="/tmp", env=env)
    d = json.loads(p.stdout)
    if d.get("is_error"):
        raise RuntimeError(str(d.get("result"))[:300])
    u = d["usage"]
    cc = u.get("cache_creation") or {}
    rec = {"in": u["input_tokens"], "cache_w": u.get("cache_creation_input_tokens", 0),
           "cache_w5m": cc.get("ephemeral_5m_input_tokens", 0), "cache_w1h": cc.get("ephemeral_1h_input_tokens", 0),
           "cache_r": u.get("cache_read_input_tokens", 0), "out": u["output_tokens"],
           "think": (u.get("output_tokens_details") or {}).get("thinking_tokens", 0),
           "sec": time.time() - t0, "api_ms": d.get("duration_api_ms"), "turns": d.get("num_turns"),
           "cost": d.get("total_cost_usd"), "model": model or MODEL}
    return d.get("result") or "", d.get("structured_output"), rec


def llm(system, prompt, schema=None, log=None, model=None):
    """Drop-in for a1_agents.llm (same return shape), with the fix."""
    err = ""
    for attempt in range(4):
        try:
            text, so, rec = raw_call(system, prompt, model=model)
            if log is not None:
                log.append({"kind": "llm", "system": system[:40], "prompt": prompt, "text": text,
                            "structured": so, **rec})
            return text, so, rec
        except Exception as e:  # noqa: BLE001
            err = str(e)[:200]
            time.sleep(3 * (attempt + 1))
    raise RuntimeError("llm failed: " + err)
