"""A8 backend: any OpenAI-compatible chat endpoint (free tiers of other model families), for every arm alike.

Used by a7_run.py when A7_BACKEND=openai. Environment:
  A7_OPENAI_BASE   e.g. https://generativelanguage.googleapis.com/v1beta/openai  (Google AI Studio)
                        https://api.groq.com/openai/v1                           (Groq)
                        https://api.mistral.ai/v1                                (Mistral)
                        https://openrouter.ai/api/v1                             (OpenRouter, ':free' models)
  A7_OPENAI_KEY    the provider's key (never committed)
  A7_OPENAI_MODEL  the provider's model id
Settings for every arm and call: temperature 0, top_p 1 (Mistral refuses greedy sampling without it), max_tokens 16000. Records prompt and completion tokens (and reasoning
tokens when the provider reports them); cost 0 on a free tier (re-price later from the token counts). Standard library.
"""

import json
import os
import time
import urllib.error
import urllib.request

BASE = os.environ.get("A7_OPENAI_BASE", "").rstrip("/")
KEY = os.environ.get("A7_OPENAI_KEY", "")
MODEL = os.environ.get("A7_OPENAI_MODEL", "")


def raw_call(system, prompt, timeout=900):
    body = json.dumps({"model": MODEL, "temperature": 0, "top_p": 1, "max_tokens": 16000,
                       "messages": [{"role": "system", "content": system},
                                    {"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(BASE + "/chat/completions", data=body,
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer " + KEY,
                                          "User-Agent": "rsos-a8/0.3.1 (+https://github.com/r-a-elu-architecture/RSOS-Language)"})
    # a User-Agent is required: some providers sit behind Cloudflare, which refuses the default Python one (error 1010)
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read())
    u = d.get("usage") or {}
    think = ((u.get("completion_tokens_details") or {}).get("reasoning_tokens")) or 0
    rec = {"in": u.get("prompt_tokens", 0), "cache_w": 0, "cache_w5m": 0, "cache_w1h": 0, "cache_r": 0,
           "out": u.get("completion_tokens", 0), "think": think, "sec": time.time() - t0, "api_ms": None,
           "turns": 1, "cost": 0.0, "model": MODEL}
    content = d["choices"][0]["message"].get("content") or ""
    if isinstance(content, list):   # reasoning models (e.g. Mistral Large 4) return chunks: keep the answer text only
        content = "".join(c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text")
    return content, None, rec


def llm(system, prompt, schema=None, log=None, model=None):
    err = ""
    for attempt in range(6):
        try:
            text, so, rec = raw_call(system, prompt)
            if log is not None:
                log.append({"kind": "llm", "system": system[:40], "prompt": prompt, "text": text,
                            "structured": so, **rec})
            return text, so, rec
        except urllib.error.HTTPError as e:          # free tiers: wait on rate limits
            err = f"HTTP {e.code}: {e.read()[:200]!r}"
            time.sleep(min(60, 10 * (attempt + 1)) if e.code == 429 else 5)
        except Exception as e:  # noqa: BLE001
            err = str(e)[:200]
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("openai-compatible call failed: " + err)


def install():
    if not (BASE and KEY and MODEL):
        raise SystemExit("set A7_OPENAI_BASE, A7_OPENAI_KEY and A7_OPENAI_MODEL")
    import a5_llm as L
    L.llm = llm
    L.raw_call = lambda system, prompt, model=None, legacy=False, timeout=900: raw_call(system, prompt, timeout)
