"""Run arms x models on a task family; results appended to a JSONL file (resumable: finished rows are skipped).
One thread per (model, arm) stream; inside a stream tasks run in a fixed order (needed for the memory role).
Example (laptop, keys set as environment variables first):
  python run.py --models openai:<model> --family warehouse --seeds 1000-1099 --arms react,rsos_11011 --out phase1.jsonl
  python run.py --models mock:0 --family staff --seeds 1-3 --arms all --out dry.jsonl      (dry run, no keys needed)"""
import argparse, json, os, threading, time, traceback
from concurrent.futures import ThreadPoolExecutor
from tasks import make, correct
from agent import run_arm

BASE = ["plain", "react", "reflexion", "selfcons", "planexec"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", required=True); ap.add_argument("--family", required=True); ap.add_argument("--seeds", required=True)
    ap.add_argument("--arms", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--design", default="v1", help="v1 = phase 1 settings (reply 700 tok, task 12000 tok, no effort); "
                    "v2 = phase 1b/1c (reply 1500, task 16000, reasoning effort low for gpt-oss/qwen3 on OpenRouter); "
                    "v3 = phase 1d and later (reply 1500, task 16000, tools declared natively, no effort parameter)")
    a = ap.parse_args()
    import agent, llm
    if a.design == "v2": agent.REPLY_TOK, agent.MAX_TOK, llm.REASONING_EFFORT = 1500, 16000, "low"
    if a.design == "v3": agent.REPLY_TOK, agent.MAX_TOK, llm.NATIVE_TOOLS = 1500, 16000, True  # no effort parameter
    print(f"design {a.design}: reply {agent.REPLY_TOK} tok, task {agent.MAX_TOK} tok, effort {llm.REASONING_EFFORT or '-'}, native tools {llm.NATIVE_TOOLS}")
    lo, hi = map(int, a.seeds.split("-")); tasks = make(a.family, range(lo, hi + 1))
    arms = BASE + ["rsos_11011", "rsos_11111", "rsos_01100", "rsos_11110"] if a.arms == "all" else a.arms.split(",")
    models = a.models.split(","); lock = threading.Lock(); done = set()
    if os.path.exists(a.out):
        for l in open(a.out):
            r = json.loads(l)
            if not r.get("error"): done.add((r["model"], r["arm"], r["task"]))  # infrastructure errors are re-run on resume
    def stream(model, arm):
        st = {}
        for t in tasks:
            if (model, arm, t["id"]) in done:
                continue
            t0 = time.time()
            try: ans, B = run_arm(arm, t, model, st); err = None
            except Exception as e: ans, B, err = None, None, repr(e)[:300]
            row = {"model": model, "arm": arm, "task": t["id"], "family": t["family"], "answer": t["answer"] if not isinstance(t["answer"], int) else int(t["answer"]),
                   "given": ans, "correct": correct(t, ans), "calls": B.calls if B else None, "tokens": B.tok if B else None,
                   "seconds": round(time.time() - t0, 1), "error": err, "lessons": len(st.get("lessons", []))}
            if os.environ.get("AGENT_TRACE") and B: row["trace"] = B.log
            with lock:
                with open(a.out, "a") as f: f.write(json.dumps(row) + "\n")
        print("done", model, arm, flush=True)
    with ThreadPoolExecutor(max_workers=len(models) * len(arms)) as ex:
        futs = [ex.submit(stream, m, arm) for m in models for arm in arms]
        for f in futs: f.result()

if __name__ == "__main__":
    main()
