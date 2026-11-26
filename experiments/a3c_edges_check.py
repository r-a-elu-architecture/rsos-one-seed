"""Reproduce A3c's per-edge channel numbers from the published, text-free count files.

The two H-pred transcript files are withheld (results/a3c_withheld.json gives their SHA-256). Their numeric content is
in results/a3c_counts_Hp.jsonl and results/a3c_replay_a3P_Hp_counts.jsonl. This check recomputes, from those files
alone, (1) H-pred's per-edge regex/BPE tokens per task, compared with results/a3c_prose.json, and (2) the offline
replay of A3's 16 P conversations, compared with results/a3c_replay_a3P_Hp.json. 0 model calls.

Run: python3 experiments/a3c_edges_check.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from a3c_edges import edges  # noqa: E402

R = os.path.join(os.path.dirname(HERE), "results")


def close(a, b):
    return abs(a - b) < 1e-9


def main():
    ok = True
    prose = json.load(open(os.path.join(R, "a3c_prose.json")))
    hp = (prose.get("tables") or prose)["Hp"]
    got, n = edges(os.path.join(R, "a3c_counts_Hp.jsonl"), "Hp")
    want = hp["per_edge_tok_bpe"]
    for e in sorted(set(got) | set(want)):
        g, w = got.get(e, [0, 0]), want.get(e, [0, 0])
        same = close(g[0], w[0]) and close(g[1], w[1])
        ok &= same
        print(f"Hp {e:12s} counts {g[0]:9.4f} / {g[1]:9.4f}   report {w[0]:9.4f} / {w[1]:9.4f}   {'ok' if same else 'MISMATCH'}")
    tot = sum(v[0] for v in got.values())
    same = close(tot, hp["channel_tok"])
    ok &= same
    print(f"Hp channel tokens per task from counts {tot:.4f}, report {hp['channel_tok']:.4f}   {'ok' if same else 'MISMATCH'}  ({n} tasks)")

    rep = json.load(open(os.path.join(R, "a3c_replay_a3P_Hp.json")))["summary"]
    rg, rn = edges(os.path.join(R, "a3c_replay_a3P_Hp_counts.jsonl"))
    rt, rb = sum(v[0] for v in rg.values()), sum(v[1] for v in rg.values())
    same = close(rt, rep["chan"]) and close(rb, rep["bpe"])
    ok &= same
    print(f"replay of A3 P through H-pred: {rt:.4f} / {rb:.4f} tokens per task, report {rep['chan']} / {rep['bpe']}   "
          f"{'ok' if same else 'MISMATCH'}  ({rn} tasks)")
    print("ALL MATCH" if ok else "MISMATCH")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
