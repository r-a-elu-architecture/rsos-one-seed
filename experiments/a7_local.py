"""A7c backend: a local open model through Ollama (http://localhost:11434), for every arm alike. $0, no CLI.

Used by a7_run.py when A7_BACKEND=ollama. Model: A7_LOCAL_MODEL (default qwen2.5:1.5b). Settings for every arm and
every call: temperature 0, seed 0, context 8192 tokens. Records prompt and output token counts; thinking 0; cost 0.
Works on Windows, macOS and Linux (standard library only).
"""

import json
import os
import time
import urllib.request

URL = os.environ.get("OLLAMA_URL", "http://localhost:11434") + "/api/chat"
MODEL = os.environ.get("A7_LOCAL_MODEL", "qwen2.5:1.5b")
OPTIONS = {"temperature": 0, "seed": 0, "num_ctx": 8192}


def raw_call(system, prompt, timeout=1800):
    body = json.dumps({"model": MODEL, "stream": False, "options": OPTIONS,
                       "messages": [{"role": "system", "content": system},
                                    {"role": "user", "content": prompt}]}).encode()
    t0 = time.time()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read())
    rec = {"in": d.get("prompt_eval_count", 0), "cache_w": 0, "cache_w5m": 0, "cache_w1h": 0, "cache_r": 0,
           "out": d.get("eval_count", 0), "think": 0, "sec": time.time() - t0, "api_ms": None, "turns": 1,
           "cost": 0.0, "model": MODEL}
    return d["message"]["content"], None, rec


def llm(system, prompt, schema=None, log=None, model=None):
    err = ""
    for attempt in range(3):
        try:
            text, so, rec = raw_call(system, prompt)
            if log is not None:
                log.append({"kind": "llm", "system": system[:40], "prompt": prompt, "text": text,
                            "structured": so, **rec})
            return text, so, rec
        except Exception as e:  # noqa: BLE001
            err = str(e)[:200]
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("ollama call failed: " + err)


def install():
    import a5_llm as L
    L.llm = llm
    L.raw_call = lambda system, prompt, model=None, legacy=False, timeout=1800: raw_call(system, prompt, timeout)
