"""run2: the sealed run.py, unchanged, with two additions made from outside (run.py, agent.py, llm.py stay byte-identical):
 1. arms rsos2 and react_b (agent2.py);
 2. OpenRouter provider pinning: every call to a pinned model goes to one fixed provider endpoint, no fallbacks, so the
    same prompt is not served by different hardware (phase 3: identical prompts at temperature 0 gave different first replies).
    The provider that actually served each call is counted and written to <out>.providers.json.
Usage (laptop):  python run2.py --design v3 --models openrouter:meta-llama/llama-4-scout,openrouter:openai/gpt-oss-20b
                 --family staff --seeds 6000-6029 --arms react,react_b,rsos2 --out quick2_staff.jsonl"""
import sys, json, collections, atexit, threading
import llm, agent, agent2

PIN = {"meta-llama/llama-4-scout": "deepinfra/fp8/flex", "openai/gpt-oss-20b": "amazon-bedrock"}
SERVED = collections.Counter(); _lock = threading.Lock(); _orig = llm._post

def _post(url, headers, body, tries=10):
    if "openrouter.ai" in url and body.get("model") in PIN:
        body = dict(body); body["provider"] = {"order": [PIN[body["model"]]], "allow_fallbacks": False}
    j = _orig(url, headers, body, tries)
    if "openrouter.ai" in url:
        p = j.get("provider"); llm.LAST["provider"] = p
        with _lock: SERVED[f"{body.get('model')} @ {p}"] += 1
    return j

llm._post = _post
import run
run.run_arm = agent2.run_arm
run.BASE = run.BASE  # unchanged

def _dump():
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "run2"
    json.dump(dict(SERVED), open(out + ".providers.json", "w"), indent=1); print("providers:", dict(SERVED))
atexit.register(_dump)

if __name__ == "__main__":
    run.main()
