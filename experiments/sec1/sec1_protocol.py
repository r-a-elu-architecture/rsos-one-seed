"""SEC1 build 2: protocol host (section 2 and layers data/message/meaning), P4 of TOP_MAP_SEC1.md, plus the P0/P2 reading.
The message is carried as the whole: @symbol#hash (green dot, U89) + the change; the receiver checks the green dot;
on a mismatch the White Dragon finds and heals only the differing chunks (U90, palace.find/heal), then opens the book.
Arms on identical worlds:
  whole      : green dot + Dragon heal + change                  (exact landing on the differing chunk)
  unchecked  : the change alone, no green dot                     (the unhealed host)
  bare       : the full new book every time                       (global change: resend everything)
P4: whole has 0 wrong adoptions over all messages AND fewer bytes per correct adoption than bare in each world.
P0 reading: whole beats unchecked in correct adoptions. P2 reading: whole beats bare in bytes. P1, P3: not measurable.
Usage: python sec1_protocol.py run"""
import sys, json, hashlib, os
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
from rsoslang.palace import Palace, encode, decode, Drift, heal

SEEDS = list(range(7100, 7116)); MSGS, LINES, BOOKS = 200, 60, 8
WORDS = "light heal beam root seed node tube sphere green gold lion dragon spine house room flow dot line".split()

def book(r): return "\n".join(" ".join(r.choice(WORDS, 6)) for _ in range(LINES))
def edit(r, text, k):
    L = text.split("\n")
    for _ in range(k): L[int(r.integers(LINES))] = " ".join(r.choice(WORDS, 6))
    return "\n".join(L)

def world(seed, q):
    r = np.random.default_rng(seed)
    S = Palace({f"b{i}": book(r) for i in range(BOOKS)}); Rx = Palace(dict(S.books))
    out = {a: {"correct": 0, "wrong": 0, "bytes": 0} for a in ["whole", "unchecked", "bare"]}
    rx = {a: Palace(dict(S.books)) for a in out}
    for _ in range(MSGS):
        sym = f"b{int(r.integers(BOOKS))}"
        if r.random() < q:                                   # the receiver's book drifted on its own
            dk = int(r.integers(1, 4)); seedd = int(r.integers(1 << 30))
            for a in rx: rx[a].books[sym] = edit(np.random.default_rng(seedd), rx[a].books[sym], dk)
        new = edit(r, S.books[sym], int(r.integers(1, 6)))
        msg = encode(S, sym, new)
        # whole
        a = "whole"; out[a]["bytes"] += len(msg.encode())
        try: got = decode(rx[a], msg, check=True)
        except Drift:
            healed, b = heal(S.books[sym], rx[a].books[sym]); out[a]["bytes"] += b
            rx[a].books[sym] = healed; got = decode(rx[a], msg, check=True)
        rx[a].books[sym] = got; out[a]["correct" if got == new else "wrong"] += 1
        # unchecked
        a = "unchecked"; out[a]["bytes"] += len(msg.encode())
        got = decode(rx[a], msg, check=False); rx[a].books[sym] = got; out[a]["correct" if got == new else "wrong"] += 1
        # bare
        a = "bare"; out[a]["bytes"] += len(new.encode()); rx[a].books[sym] = new; out[a]["correct"] += 1
        S.books[sym] = new
    return out

if __name__ == "__main__" and sys.argv[1] == "run":
    from scipy.stats import binomtest
    def sp(x): x = np.asarray(x); w = int(np.sum(x > 0)); return {"wins": w, "of": len(x), "p": float(binomtest(w, len(x), 0.5, alternative="greater").pvalue)}
    R = {"code_sha256": hashlib.sha256(open(__file__, "rb").read()).hexdigest()}; rows = []
    for q in [0.1, 0.3, 0.5]:
        for s in SEEDS:
            o = world(s, q); rows.append({"q": q, "seed": s, **{f"{a}_{k}": v for a, d in o.items() for k, v in d.items()}})
    bpc = lambda r, a: r[f"{a}_bytes"] / max(1, r[f"{a}_correct"])
    R["P4_whole_zero_wrong"] = {"wrong_total": int(sum(r["whole_wrong"] for r in rows)), "pass": all(r["whole_wrong"] == 0 for r in rows)}
    R["P4_whole_fewer_bytes_per_correct_than_bare"] = sp([bpc(r, "bare") - bpc(r, "whole") for r in rows])
    R["P0_reading_whole_beats_unchecked_correct"] = sp([r["whole_correct"] - r["unchecked_correct"] for r in rows])
    R["unchecked_wrong_total"] = int(sum(r["unchecked_wrong"] for r in rows))
    R["bytes_per_correct_mean"] = {a: float(np.mean([bpc(r, a) for r in rows])) for a in ["whole", "unchecked", "bare"]}
    R["P1"] = R["P3"] = "not measurable in this host"
    json.dump(rows, open("RAW_SEC1_protocol.json", "w")); json.dump(R, open("RESULTS_SEC1_protocol.json", "w"), indent=1)
    print(json.dumps(R, indent=1))
