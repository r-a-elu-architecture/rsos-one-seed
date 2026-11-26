"""A3 resumable runner (PREREGISTRATION_A3.md).

The first batch stopped at 53/64 task runs (account usage limit). Finished runs left their full transcripts
(every prompt, output and usage) but run_task's result records were only written at the end. This runner:

1. replays every finished run from its transcript: the harness is deterministic given the LLM outputs, so the
   recorded outputs are fed back in order and every prompt is asserted to equal the recorded prompt; usage and
   seconds come from the recording; wall_sec of a replayed run = sum of its recorded LLM call seconds;
2. runs live only the (cond, seed) pairs that have no transcript, appending each result as it completes;
3. writes results/a3_runs.json in the A1 format.

    python experiments/a3_run.py
"""

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import a1_agents as A                      # noqa: E402

CONDS = ["P", "A", "D", "E"]
SEEDS = list(range(100, 108)) + list(range(300, 308))
RES = os.path.join(A.ROOT, "results", "a3_results.jsonl")
TRANS = os.path.join(A.ROOT, "results", "a3_transcripts.jsonl")


def replay(rec):
    queue = list(rec["calls"])
    real = A.llm

    def fake(system, prompt, schema=None, log=None):
        c = queue.pop(0)
        assert c["prompt"] == prompt and c["system"] == system[:40], "replay diverged"
        r = {k: c[k] for k in ("in", "cache_w", "cache_r", "out", "sec", "api_ms", "turns", "cost")}
        if log is not None:
            log.append(c)
        return c["text"], c["structured"], r

    A.llm = fake
    try:
        res = A.run_task(rec["cond"], rec["seed"])
    finally:
        A.llm = real
    assert not queue, "unused recorded calls"
    res["wall_sec"] = sum(c["sec"] for c in rec["calls"])
    res["replayed"] = True
    return res


def main():
    done = {}
    if os.path.exists(RES):
        for line in open(RES):
            r = json.loads(line); done[(r["cond"], r["seed"])] = r
    os.environ["A_TRANSCRIPTS"] = os.devnull            # replays must not duplicate transcripts
    for line in open(TRANS):
        rec = json.loads(line)
        if (rec["cond"], rec["seed"]) not in done:
            r = replay(rec); done[(r["cond"], r["seed"])] = r
            with open(RES, "a") as f:
                f.write(json.dumps(r) + "\n")
    os.environ["A_TRANSCRIPTS"] = TRANS
    todo = [(c, s) for s in SEEDS for c in CONDS if (c, s) not in done]
    print(f"replayed/loaded {len(done)}, live {len(todo)}: {todo}", flush=True)
    with ThreadPoolExecutor(int(os.environ.get("A3_WORKERS", "6"))) as ex:
        futs = [ex.submit(A.run_task, c, s) for c, s in todo]
        for fu in as_completed(futs):
            r = fu.result(); r["replayed"] = False; done[(r["cond"], r["seed"])] = r
            with open(RES, "a") as f:
                f.write(json.dumps(r) + "\n")
    sc = A.scaffold()
    runs = [done[(c, s)] for s in SEEDS for c in CONDS]
    json.dump({"model": A.MODEL, "scaffold": sc, "runs": runs}, open(os.path.join(A.ROOT, "results", "a3_runs.json"), "w"),
              indent=1)
    print("wrote a3_runs.json", len(runs))


if __name__ == "__main__":
    main()
