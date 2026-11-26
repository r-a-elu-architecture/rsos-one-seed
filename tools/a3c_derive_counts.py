#!/usr/bin/env python3
"""Derive text-free count files from the two withheld A3c H-pred transcript files (owner decision, 18 Nov 2026).

H-pred sends its arithmetic-coded bits as words from a 47,424-word alphabet, so coded messages can contain arbitrary
words, including clinical terms, as code digits. The transcripts stay private; this script publishes what the
analysis needs: per message and per model call, every numeric field and no text. It also records the SHA-256 of the
withheld files, so they can be verified if they are ever released.

Usage (private repo, where the transcripts exist): python3 -I tools/a3c_derive_counts.py
"""
import hashlib
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(ROOT, "results")
PAIRS = [("a3c_transcripts_Hp.jsonl", "a3c_counts_Hp.jsonl"),
         ("a3c_replay_a3P_Hp_transcripts.jsonl", "a3c_replay_a3P_Hp_counts.jsonl")]
MSG_KEEP = ("step", "attempt", "from", "to", "kind", "tok", "bpe", "bytes")
CALL_KEEP = ("kind", "in", "cache_w", "cache_r", "out", "sec", "api_ms", "turns", "cost")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    withheld = {}
    for src, dst in PAIRS:
        sp = os.path.join(R, src)
        withheld[src] = {"sha256": sha256(sp), "bytes": os.path.getsize(sp), "derived": dst}
        with open(sp) as f, open(os.path.join(R, dst), "w") as g:
            for line in f:
                t = json.loads(line)
                out = {"cond": t["cond"], "seed": t["seed"], "tag": t["tag"],
                       "msgs": [{k: m[k] for k in MSG_KEEP if k in m} for m in t["msgs"]],
                       "calls": [{k: c[k] for k in CALL_KEEP if k in c} for c in t.get("calls", [])]}
                g.write(json.dumps(out, sort_keys=True) + "\n")
    with open(os.path.join(R, "a3c_withheld.json"), "w") as f:
        json.dump({"note": "Withheld A3c H-pred transcripts (coded messages use arbitrary alphabet words as code digits). "
                           "Text-free count files are published in their place; available on request for verification.",
                   "files": withheld}, f, indent=1, sort_keys=True)
        f.write("\n")
    print(json.dumps(withheld, indent=1))


if __name__ == "__main__":
    main()
