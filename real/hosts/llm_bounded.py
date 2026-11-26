"""Bounded model calls for the LLM rows (REAL3 v2, 25 Nov 2026). experiments/agents/llm.py is sealed (phase 3) and is
not changed; this module only replaces llm._post FOR THE DURATION OF ONE CALL with a bounded version, then restores it.

Why: llm._post retries 10 times with a 120 s request timeout and back-off up to 60-90 s (retry-after honoured up to 90 s):
one call that keeps meeting 429 / 5xx / timeouts can block ~25-35 minutes, and the host's one retry doubles that. The
AI-agents Llama 3.1 8B cloud job died after 1h49m (REAL1: likely 429 retry exhaustion).

Bounded call (every number below applies identically to every mode and standard; none touches what a successful call
returns):
  - per-request timeout REQ_TIMEOUT = 45 s;
  - at most TRIES = 4 requests per call, back-off min(8, 2^k) + jitter (retry-after honoured, capped at 15 s);
  - a wall deadline per call DEADLINE = 100 s across its tries (no sleep beyond it);
  - circuit breaker: after BREAK_AFTER = 3 consecutive failed calls in the process, each further call gets ONE request
    (timeout 30 s) until a call succeeds again (a provider that is down does not cost minutes per call).
  - non-retryable HTTP errors (400 / 401 / 402 / 403 / 404 / 422) raise at once, as in llm._post.
On failure the caller records the call as FAILED (counted in report()["failed_calls"], reason logged); nothing crashes.
Env overrides (cloud tuning only): REAL3_LLM_TRIES, REAL3_LLM_TIMEOUT, REAL3_LLM_DEADLINE."""
import os, sys, time, random, contextlib
import requests
_AG = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "experiments", "agents"))
if _AG not in sys.path: sys.path.insert(0, _AG)
import llm                                      # noqa: E402

TRIES = int(os.environ.get("REAL3_LLM_TRIES", "4"))
REQ_TIMEOUT = float(os.environ.get("REAL3_LLM_TIMEOUT", "45"))
DEADLINE = float(os.environ.get("REAL3_LLM_DEADLINE", "100"))
BREAK_AFTER = 3
RETRY_CODES = (408, 409, 429, 500, 502, 503, 504, 529)
STATE = {"consecutive_fail": 0, "calls": 0, "failed": 0, "requests": 0, "retries": 0, "seconds_waited": 0.0,
         "broken_calls": 0, "last_reason": ""}


def _bounded_post_factory(tries, timeout, deadline):
    t_end = time.time() + deadline

    def _post(url, headers, body, tries_ignored=10):
        last = "no request made"
        for k in range(tries):
            left = t_end - time.time()
            if left <= 1: last = f"deadline {deadline:.0f}s reached ({last})"; break
            try:
                STATE["requests"] += 1
                r = requests.post(url, headers=headers, json=body, timeout=min(timeout, left))
                if r.status_code == 200: return r.json()
                if r.status_code in RETRY_CODES:
                    last = f"HTTP {r.status_code}: {r.text[:200]}"
                    ra = r.headers.get("retry-after")
                    try: wait = float(ra) + 1 if ra else min(8, 2 ** k) + random.random()
                    except ValueError: wait = min(8, 2 ** k) + random.random()
                    wait = min(15.0, wait, max(0.0, t_end - time.time() - 1))
                    if k < tries - 1 and wait > 0:
                        STATE["retries"] += 1; STATE["seconds_waited"] += wait; time.sleep(wait)
                    continue
                raise llm.LLMError(f"{r.status_code}: {r.text[:300]}", r.text)
            except requests.RequestException as e:
                last = f"{type(e).__name__}: {str(e)[:200]}"
                wait = min(8, 2 ** k, max(0.0, t_end - time.time() - 1))
                if k < tries - 1 and wait > 0:
                    STATE["retries"] += 1; STATE["seconds_waited"] += wait; time.sleep(wait)
        raise llm.LLMError(f"bounded retries exhausted ({tries} tries / {deadline:.0f}s): {last}")
    return _post


@contextlib.contextmanager
def bounded():
    """Within the block, llm._post is the bounded version (restored afterwards, also on exceptions)."""
    broken = STATE["consecutive_fail"] >= BREAK_AFTER
    tries, timeout, deadline = (1, min(30.0, REQ_TIMEOUT), 35.0) if broken else (TRIES, REQ_TIMEOUT, DEADLINE)
    STATE["broken_calls"] += broken
    old = llm._post; llm._post = _bounded_post_factory(tries, timeout, deadline)
    try: yield
    finally: llm._post = old


def chat(spec, system, messages, **kw):
    """llm.chat under the bound. Raises on failure (the caller logs and records it); updates the circuit breaker."""
    STATE["calls"] += 1
    try:
        with bounded():
            out = llm.chat(spec, system, messages, **kw)
    except Exception as e:      # noqa: BLE001
        STATE["consecutive_fail"] += 1; STATE["failed"] += 1; STATE["last_reason"] = f"{type(e).__name__}: {str(e)[:200]}"
        raise
    STATE["consecutive_fail"] = 0
    return out


def retry_worthwhile(e):
    """The host's single second try (empty assistant turns replaced) is only worth making for a request the provider
    rejected as malformed (400 / 422) or a reply that could not be read (KeyError / TypeError / ...); never after a
    bounded-retry exhaustion (rate limit, timeouts, 5xx), which would only double the wait."""
    msg = str(e)
    if "bounded retries exhausted" in msg: return False
    if isinstance(e, llm.LLMError): return msg[:3] in ("400", "422")
    return True


def summary():
    return dict(STATE)
