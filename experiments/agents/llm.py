"""Model clients over plain HTTPS (no SDKs). Keys only from environment variables, never from files or arguments:
OPENAI_API_KEY, GEMINI_API_KEY, ANTHROPIC_API_KEY. Model spec: provider:model_name (e.g. openai:<name>,
google:<name>, anthropic:<name>, ollama:<local model, free>, groq:<open model>, openrouter:<model>, cerebras:<open model>, mock:0).
Keys for those: GROQ_API_KEY, OPENROUTER_API_KEY, CEREBRAS_API_KEY. Every call returns (text, input_tokens, output_tokens)."""
import re
import os, time, json, random
import requests

REASONING_EFFORT = os.environ.get("REASONING_EFFORT", "")  # set by run.py from the sealed design
LAST = {}  # finish reason of the last call (logged in traces)

class LLMError(Exception):
    def __init__(s, msg, body=""): super().__init__(msg); s.body = body

def _post(url, headers, body, tries=10):
    for k in range(tries):
        try:
            r = requests.post(url, headers=headers, json=body, timeout=120)
            if r.status_code == 200: return r.json()
            if r.status_code in (408, 409, 429, 500, 502, 503, 504, 529):
                ra = r.headers.get("retry-after")
                try: wait = float(ra) + 1 if ra else min(60, 2 ** k + random.random())
                except ValueError: wait = min(60, 2 ** k + random.random())
                time.sleep(min(90, wait)); continue
            raise LLMError(f"{r.status_code}: {r.text[:300]}", r.text)
        except requests.RequestException as e:
            if k == tries - 1: raise LLMError(str(e))
            time.sleep(2 ** k)
    raise LLMError("retries exhausted")

NATIVE_TOOLS = False  # design v3: declare the task's tools natively (one string argument); calls are rewritten to text actions

def tool_defs(names):
    from tasks import TOOL_HELP
    return [{"type": "function", "function": {"name": n, "description": TOOL_HELP[n], "parameters": {"type": "object",
             "properties": {"args": {"type": "string", "description": "the text inside the parentheses, e.g. product=lamp"}},
             "required": ["args"]}}} for n in names]

def chat(spec, system, messages, max_tokens=700, temperature=0.0, tools=None):
    """messages: list of {"role": "user"|"assistant", "content": str}."""
    prov, name = spec.split(":", 1)
    if prov == "openai":
        body = {"model": name, "messages": [{"role": "system", "content": system}] + messages, "max_completion_tokens": max_tokens}
        if temperature is not None and not name.startswith(("o1", "o3", "o4", "gpt-5")): body["temperature"] = temperature
        j = _post("https://api.openai.com/v1/chat/completions", {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"}, body)
        u = j.get("usage", {}); return j["choices"][0]["message"].get("content") or "", u.get("prompt_tokens", 0), u.get("completion_tokens", 0)
    if prov in ("groq", "openrouter", "cerebras"):
        url, key = {"groq": ("https://api.groq.com/openai/v1/chat/completions", "GROQ_API_KEY"),
                    "openrouter": ("https://openrouter.ai/api/v1/chat/completions", "OPENROUTER_API_KEY"),
                    "cerebras": ("https://api.cerebras.ai/v1/chat/completions", "CEREBRAS_API_KEY")}[prov]
        body = {"model": name, "messages": [{"role": "system", "content": system}] + messages, "max_tokens": max_tokens, "temperature": temperature}
        if prov == "openrouter" and REASONING_EFFORT and any(x in name for x in ("gpt-oss", "qwen3")):
            body["reasoning"] = {"effort": REASONING_EFFORT}  # phase 1: hidden reasoning used the whole reply budget (empty replies)
        if NATIVE_TOOLS and tools: body["tools"] = tool_defs(tools); body["tool_choice"] = "auto"
        hdr = {"Authorization": f"Bearer {os.environ[key]}"}
        for k in range(3):
            try: j = _post(url, hdr, body); break
            except LLMError as e:
                # gpt-oss on Groq sometimes emits a native tool call although no tools are declared (400 "model called a
                # tool"). The harness uses text actions for every arm, so ask again with a plain-text reminder.
                if "called a tool" not in e.body or k == 2:
                    if "called a tool" in e.body:
                        try: fg = json.loads(e.body)["error"].get("failed_generation", "")
                        except Exception: fg = ""
                        return str(fg), 0, 0
                    raise
                body = dict(body); body["messages"] = [{"role": "system", "content": system + "\nNever use native function or tool "
                    "calls. Write the action as plain text on the last line, for example: ACTION: lookup(Lior)"}] + messages
                body["temperature"] = 0.3
        msg = j["choices"][0]["message"]; u = j.get("usage", {}); txt = msg.get("content") or ""
        LAST["finish"] = j["choices"][0].get("finish_reason")
        if msg.get("tool_calls") and not re.search(r"^\s*(ACTION|ANSWER):", txt, re.M):  # native tool call -> text action
            fn = msg["tool_calls"][0].get("function", {}); a = fn.get("arguments", ""); nm = fn.get("name", "").split(".")[-1]
            try:
                d = json.loads(a) if a else {}
                if isinstance(d, dict) and "args" in d: a = str(d["args"])
                elif isinstance(d, dict) and {"field", "value"} <= set(d): a = f"{d['field']}={d['value']}"
                elif isinstance(d, dict) and len(d) == 1 and nm in ("filter", "orders_where"): a = f"{list(d)[0]}={list(d.values())[0]}"
                elif isinstance(d, dict): a = ", ".join(", ".join(map(str, v)) if isinstance(v, list) else str(v) for v in d.values())
                else: a = str(d)
            except Exception: pass
            txt = (txt.strip() + "\n" if txt.strip() else "") + f"ACTION: {nm}({a})"; LAST["finish"] = "tool_call_rewritten"
        if not txt.strip():  # diagnosis of empty replies (logged in traces)
            LAST["finish"] = f"{LAST['finish']}|empty|reasoning={len(str(msg.get('reasoning') or ''))}|tool_calls={len(msg.get('tool_calls') or [])}"
            LAST["reasoning"] = str(msg.get("reasoning") or "")[:300]
        txt = re.sub(r"<think>.*?(</think>|$)", "", txt, flags=re.S).strip()  # reasoning models: keep only the answer
        return txt, u.get("prompt_tokens", 0), u.get("completion_tokens", 0)
    if prov == "anthropic":
        body = {"model": name, "system": system, "messages": messages, "max_tokens": max_tokens, "temperature": temperature}
        j = _post("https://api.anthropic.com/v1/messages", {"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"}, body)
        u = j.get("usage", {}); return "".join(b.get("text", "") for b in j.get("content", []) if b.get("type") == "text"), u.get("input_tokens", 0), u.get("output_tokens", 0)
    if prov == "google":
        body = {"systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user" if m["role"] == "user" else "model", "parts": [{"text": m["content"]}]} for m in messages],
                "generationConfig": {"maxOutputTokens": max_tokens, "temperature": temperature}}
        j = _post(f"https://generativelanguage.googleapis.com/v1beta/models/{name}:generateContent", {"x-goog-api-key": os.environ["GEMINI_API_KEY"]}, body)
        u = j.get("usageMetadata", {}); c = (j.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
        return "".join(p.get("text", "") for p in c), u.get("promptTokenCount", 0), u.get("candidatesTokenCount", 0)
    if prov == "ollama":
        body = {"model": name, "messages": [{"role": "system", "content": system}] + messages, "stream": False,
                "options": {"temperature": temperature, "num_predict": max_tokens}}
        j = _post(os.environ.get("OLLAMA_URL", "http://localhost:11434") + "/api/chat", {}, body)
        return j.get("message", {}).get("content", ""), j.get("prompt_eval_count", 0), j.get("eval_count", 0)
    if prov == "mock":
        return mock(system, messages), 50, 20
    raise LLMError(f"unknown provider {prov}")

def mock(system, messages):
    """Code-path test only: random tool calls and answers. Never used for results."""
    last = messages[-1]["content"]; r = random.Random(hash(last) % 10 ** 9)
    if "Verify" in last or "verify" in last: return r.choice(["VERDICT: OK", "VERDICT: WRONG because a step was off"])
    if "PLAN" in last: return "PLAN: 1. look up 2. compute 3. answer"
    if "LESSON" in last: return "LESSON: recompute totals with the calculator before answering."
    return r.choice(["ACTION: calc(2+3*4)", "ACTION: list_names()", f"ANSWER: {r.randint(1, 500)}", "ACTION: calc(10/0)"])
