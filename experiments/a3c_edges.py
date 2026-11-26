"""Per-edge regex/BPE tokens per task from an A3c transcripts file."""
import json
import sys
from collections import defaultdict

EDGE = {("planner", "worker"): "instruction", ("worker", "checker"): "edits", ("checker", "worker"): "door",
        ("checker", "planner"): "forward"}


def edges(path, cond=None):
    tot, n = defaultdict(lambda: [0, 0]), 0
    for line in open(path):
        t = json.loads(line)
        if cond and t["cond"] != cond:
            continue
        n += 1
        for m in t["msgs"]:
            e = "heal" if m["kind"] == "heal" else EDGE.get((m["from"], m["to"]), "other")
            tot[e][0] += m["tok"]; tot[e][1] += m["bpe"]
    return {k: [v[0] / n, v[1] / n] for k, v in tot.items()}, n


if __name__ == "__main__":
    print(edges(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
