"""A3c priming corpus (design: results/a3c_dragon_design.json, priming_corpus): 32 full A3b H-dragon task runs on
seeds 500-531 (disjoint from the test seeds), same agents and prompts, before any test-seed run. Resumable.

    python experiments/a3c_prime_runs.py   -> results/a3c_priming_results.jsonl, results/a3c_priming_transcripts.jsonl
"""

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import a1_agents as A                      # noqa: E402
import a3b_hologram as H                   # noqa: E402
from a3b_hdragon import HDragon            # noqa: E402

SEEDS = list(range(500, 532))
RES = os.path.join(A.ROOT, "results", "a3c_priming_results.jsonl")
os.environ["A_TRANSCRIPTS"] = os.path.join(A.ROOT, "results", "a3c_priming_transcripts.jsonl")


def main():
    done = set()
    if os.path.exists(RES):
        done = {json.loads(x)["seed"] for x in open(RES)}
    todo = [s for s in SEEDS if s not in done]
    print("done", len(done), "todo", len(todo), flush=True)
    with ThreadPoolExecutor(int(os.environ.get("A3C_WORKERS", "8"))) as ex:
        futs = [ex.submit(H.run_task, HDragon(), s, "prime") for s in todo]
        for fu in as_completed(futs):
            r = fu.result()
            with H._lock:
                with open(RES, "a") as f:
                    f.write(json.dumps(r) + "\n")


if __name__ == "__main__":
    main()
