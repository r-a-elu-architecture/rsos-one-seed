"""A3c runner (PREREGISTRATION_A3C.md): priming build, offline replays, live runs of H-pred (Hp) and H-local (Hl).

The A3b harness `a3b_hologram.run_task` is used unchanged; the codecs are new (a3c_hpred, a3c_hlocal).

    python experiments/a3c_run.py prime              # build the frozen H-pred model from seeds 500-531
    python experiments/a3c_run.py replay Hp|Hl SRC   # offline: SRC = smoke | prime | a3P (prompts asserted)
    python experiments/a3c_run.py run Hp|Hl          # live, test seeds 100-107, 300-307, resumable
"""

import hashlib
import json
import os
import pickle
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import a1_agents as A                      # noqa: E402
import a3b_hologram as H                   # noqa: E402
from a1_analyse import FRACS               # noqa: E402
from a3c_coder import Undecodable          # noqa: E402
import a3c_hpred as P                      # noqa: E402

R = os.path.join(A.ROOT, "results")
SEEDS = list(range(100, 108)) + list(range(300, 308))
PRIME_SEEDS = list(range(500, 532))
FROZEN = os.path.join(R, "a3c_hpred_frozen.pkl")


def with_trunc(cls):
    """Adds the truncation check of every worker -> checker message, run in-line with the live codec state
    (A3b ran it offline from the transcripts; the codec here is adaptive, so the check runs where the state is)."""
    class T(cls):
        def new_task(self, init_text):
            super().new_task(init_text)
            self.trunc = {str(f): {"detected": 0, "silent_wrong": 0, "correct": 0} for f in FRACS}

        def enc_edits(self, old_text, new_text):
            m = super().enc_edits(old_text, new_text)
            keep = dict(self.pending_edits)
            for f in FRACS:
                cut = m[:int(len(m) * (1 - f))]
                try:
                    got = self.dec_edits(cut, old_text)
                except Exception:  # noqa: BLE001
                    self.trunc[str(f)]["detected"] += 1; continue
                self.trunc[str(f)]["correct" if (cut == m or got == new_text) else "silent_wrong"] += 1
            self.pending_edits = keep
            return m
    T.__name__ = cls.__name__
    return T


def codec_of(name, primed=True):
    if name == "Hp":
        c = with_trunc(P.HPred)()
    elif name == "Hl":
        import a3c_hlocal
        c = with_trunc(a3c_hlocal.HLocal)()
    else:
        raise ValueError(name)
    if primed:
        c.primed = load_primed()
    return c


_PR = None


def load_primed():
    global _PR
    if _PR is None:
        _PR = pickle.load(open(FROZEN, "rb"))
    return _PR


def replay(rec, codec, seed, tag):
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
        res = H.run_task(codec, seed, tag=tag)
    finally:
        A.llm = real
    assert not queue, "unused recorded calls"
    return res


def attach(res, codec):
    res["codec_stats"] = dict(codec.stats)
    res["trunc"] = codec.trunc
    return res


def prime():
    """Design: replay the 32 priming runs in seed order through the live codec in update mode (counts kept across
    runs, task history reset), then halve every count once and freeze."""
    os.environ["A_TRANSCRIPTS"] = os.devnull
    recs = {json.loads(x)["seed"]: json.loads(x) for x in open(os.path.join(R, "a3c_priming_transcripts.jsonl"))}
    assert sorted(recs) == PRIME_SEEDS, sorted(recs)
    c = P.HPred()
    c.persist = True
    c.M = P.Model()
    t0 = time.time()
    for s in PRIME_SEEDS:
        replay(recs[s], c, s, "prime")
    c.M.halve_all()
    pickle.dump(c.M, open(FROZEN, "wb"))
    sz = os.path.getsize(FROZEN)
    corpus = [x["text"].strip() for s in PRIME_SEEDS for x in recs[s]["calls"]
              if x["system"].startswith("You are the PLANNER")]
    reasons = []
    for s in PRIME_SEEDS:
        for x in recs[s]["calls"]:
            if x["system"].startswith("You are the CHECKER"):
                g, r = A.parse_verdict(x["text"], x["structured"])
                if not g:
                    reasons.append(r)
    allt = "\n".join(corpus + reasons)
    info = {"frozen_bytes": sz, "frozen_sha256": hashlib.sha256(open(FROZEN, "rb").read()).hexdigest(),
            "n_instr": len(corpus), "n_reasons": len(reasons), "corpus_bytes": len(allt.encode()),
            "corpus_regex_tok": A.ntok(allt), "corpus_bpe": H.bpe(allt), "sec": time.time() - t0,
            "vocab": len(c.M.vocab), "ppm_contexts": len(c.M.ppm)}
    json.dump(info, open(os.path.join(R, "a3c_priming_info.json"), "w"), indent=1)
    print(json.dumps(info, indent=1))


def src_records(src):
    if src == "smoke":
        return [json.loads(x) for x in open(os.path.join(R, "a3b_smoke_transcripts.jsonl"))
                if json.loads(x)["cond"] == "Hd"]
    if src == "prime":
        return [json.loads(x) for x in open(os.path.join(R, "a3c_priming_transcripts.jsonl"))]
    if src == "a3P":
        return [json.loads(x) for x in open(os.path.join(R, "a3_transcripts.jsonl")) if json.loads(x)["cond"] == "P"]
    raise ValueError(src)


def replay_src(name, src, primed=True, limit=None):
    os.environ["A_TRANSCRIPTS"] = os.path.join(R, f"a3c_replay_{src}_{name}_transcripts.jsonl")
    if os.path.exists(os.environ["A_TRANSCRIPTS"]):
        os.remove(os.environ["A_TRANSCRIPTS"])
    out = []
    for rec in src_records(src)[:limit]:
        c = codec_of(name, primed)
        out.append(attach(replay(rec, c, rec["seed"], "replay_" + src), c))
    n = len(out)
    st = lambda k: sum(r["codec_stats"][k] for r in out)  # noqa: E731
    summ = {"runs": n, "chan": sum(r["channel_tok"] for r in out) / n, "bpe": sum(r["channel_bpe"] for r in out) / n,
            "success": sum(r["success"] for r in out), "replica": sum(r["replica_success"] for r in out),
            "heal0": sum(e["healed_zero_call"] for r in out for e in r["drift"]),
            "instr_bpc": st("instr_bits") / max(1, st("instr_chars")),
            "reason_bpc": st("reason_bits") / max(1, st("reason_chars")),
            "edits_fallback": st("edits_fallback"),
            "trunc_silent": sum(v["silent_wrong"] for r in out for v in r["trunc"].values())}
    json.dump({"summary": summ, "runs": out}, open(os.path.join(R, f"a3c_replay_{src}_{name}.json"), "w"), indent=1)
    print(name, src, json.dumps(summ))
    return summ


def main_run(name):
    res = os.path.join(R, f"a3c_results_{name}.jsonl")
    os.environ["A_TRANSCRIPTS"] = os.path.join(R, f"a3c_transcripts_{name}.jsonl")
    done = {}
    if os.path.exists(res):
        for line in open(res):
            r = json.loads(line); done[r["seed"]] = r
    todo = [s for s in SEEDS if s not in done]
    print(f"{name}: loaded {len(done)}, live {len(todo)}", flush=True)

    def one(s):
        c = codec_of(name)
        return attach(H.run_task(c, s), c)

    with ThreadPoolExecutor(int(os.environ.get("A3C_WORKERS", "8"))) as ex:
        futs = [ex.submit(one, s) for s in todo]
        for fu in as_completed(futs):
            r = fu.result(); done[r["seed"]] = r
            with H._lock:
                with open(res, "a") as f:
                    f.write(json.dumps(r) + "\n")
    print("done", len(done))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "prime":
        prime()
    elif cmd == "replay":
        replay_src(sys.argv[2], sys.argv[3], primed=os.environ.get("A3C_UNPRIMED") != "1",
                   limit=int(sys.argv[4]) if len(sys.argv) > 4 else None)
    elif cmd == "run":
        main_run(sys.argv[2])
