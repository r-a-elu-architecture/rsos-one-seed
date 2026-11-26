"""A3c analysis: C1-C4 (PREREGISTRATION_A3C.md) -> results/a3c_prose.json (common.save, hash in the report).

D and H-dragon are re-used from A3 / A3b after results/a3c_reuse.json passed. H-pred (Hp) and H-local (Hl) come
from results/a3c_results_{Hp,Hl}.jsonl + transcripts. Truncation was checked in-line on every worker -> checker
message (5 cut fractions, full strict decode + chk6) and is stored per run.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import a3b_hologram as H                   # noqa: E402
from a3c_edges import edges                # noqa: E402
from common import bootstrap_ci, save      # noqa: E402

if H._BPE is None:
    sys.exit("a3c_analyse: tiktoken (o200k_base) is required")

R = os.path.join(os.path.dirname(HERE), "results")
D_TOK, D_BPE = 1468.0, 1860.0          # A3 tent (re-used; BPE recount from A3b)
HD = {"tok": 932.4375, "bpe": 1023.3125}
PRED = {"Hp": 276, "Hl": 205}


def load(name):
    p = os.path.join(R, f"a3c_results_{name}.jsonl")
    if not os.path.exists(p):
        return []
    rs = {}
    for line in open(p):
        r = json.loads(line); rs[r["seed"]] = r
    return [rs[s] for s in sorted(rs)]


def summ(name, rs):
    n = len(rs)
    mean = lambda k: sum(r[k] for r in rs) / n          # noqa: E731
    ev = [e for r in rs for e in r["drift"]]
    st = lambda k: sum(r["codec_stats"].get(k, 0) for r in rs)  # noqa: E731
    tr = {}
    for r in rs:
        for f, v in r["trunc"].items():
            d = tr.setdefault(f, {"detected": 0, "silent_wrong": 0, "correct": 0})
            for k in d:
                d[k] += v[k]
    ed, _ = edges(os.path.join(R, f"a3c_transcripts_{name}.jsonl"), name)
    out = {"n": n, "channel_tok": mean("channel_tok"), "channel_tok_ci95": bootstrap_ci([r["channel_tok"] for r in rs]),
           "channel_bpe": mean("channel_bpe"), "channel_bytes": mean("channel_bytes"),
           "x_D_regex": mean("channel_tok") / D_TOK, "x_D_bpe": mean("channel_bpe") / D_BPE,
           "x_Hdragon_regex": mean("channel_tok") / HD["tok"],
           "per_edge_tok_bpe": ed,
           "exact": sum(r["success"] for r in rs), "replica": sum(r["replica_success"] for r in rs),
           "wrong_final_lines": sum(len(r["final_errors"]) for r in rs),
           "steps_failed": sum(r["steps_failed"] for r in rs),
           "drift_events": len(ev), "heal0": sum(e["healed_zero_call"] for e in ev),
           "drift_in_any_copy_end": sum(e["in_any_copy_final"] for e in ev),
           "trunc": tr, "trunc_total": sum(sum(v.values()) for v in tr.values()),
           "trunc_silent": sum(v["silent_wrong"] for v in tr.values()),
           "billed_tok": mean("billed_tok"), "llm_calls": mean("n_calls"), "wall_sec": mean("wall_sec"),
           "cost_usd_total": sum(r["cost_usd"] for r in rs),
           "instr_bpc": st("instr_bits") / max(1, st("instr_chars")),
           "reason_bpc": st("reason_bits") / max(1, st("reason_chars")) if st("reason_chars") else None,
           "n_reasons": st("n_reason"), "edits_fallback": st("edits_fallback"), "nak": st("nak"),
           "mode_llm": st("mode_llm"), "mode_hpred": st("mode_hpred"), "llm_ctx_fallback": st("llm_ctx_fallback")}
    return out


def local_calls():
    """H-local forward passes, recounted exactly from the transcripts: the encoder runs the model on every prose
    message (1 prefill + one pass per payload token before EOT), the decoder again when the message is in LLM mode
    (mode read off the wire message's first symbol); +1 pass for the preamble per process. CPU: sampler log."""
    import a3c_hlocal as L
    from a3c_coder import Dec
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(L.MODEL_ID, revision=L.REVISION)
    passes, toks, msgs, llm = 0, 0, 0, 0
    for line in open(os.path.join(R, "a3c_transcripts_Hl.jsonl")):
        t = json.loads(line)
        prose = [c["text"].strip() for c in t["calls"] if c["system"].startswith("You are the PLANNER")]
        wires = [m["text"] for m in t["msgs"] if m["from"] == "planner" and m["to"] == "worker"]
        for c in t["calls"]:
            if c["system"].startswith("You are the CHECKER"):
                import a1_agents as A
                g, r = A.parse_verdict(c["text"], c["structured"])
                if not g:
                    prose.append(r)
        wires += [m["text"] for m in t["msgs"] if m["from"] == "checker" and m["to"] == "worker" and m["text"] != "+"]
        for x in prose:
            n = len(tok.encode(x, add_special_tokens=False))
            passes += 1 + n; toks += n; msgs += 1
        for w in wires:
            if Dec(w).sym(["L", "P"], [15, 1]) == "L":
                llm += 1
    return {"prose_messages": msgs, "llm_mode_messages": llm, "encoder_passes": passes, "payload_tokens": toks}


def verdicts(s, name):
    integ = s["heal0"] == 48 and s["replica"] == 16 and s["trunc_silent"] == 0
    if name == "Hp":
        c1 = s["channel_tok"] <= 0.5 * D_TOK and s["channel_bpe"] <= 0.5 * D_BPE and integ
        c2 = s["exact"] >= 16
        c4 = abs(PRED["Hp"] - s["channel_tok"]) <= 0.5 * s["channel_tok"]
        return {"C1": c1, "C2": c2, "C4": c4, "integrity": integ}
    c3 = s["channel_tok"] <= 0.2 * D_TOK and s["channel_bpe"] <= 0.2 * D_BPE and integ
    c4l = abs(PRED["Hl"] - s["channel_tok"]) <= 0.5 * s["channel_tok"]
    return {"C3": c3, "C4_analogue_Hl": c4l, "integrity": integ, "exact_ge_16": s["exact"] >= 16}


def main():
    reuse = json.load(open(os.path.join(R, "a3c_reuse.json")))
    out = {"reuse": reuse, "D": {"tok": D_TOK, "bpe": D_BPE}, "Hdragon": HD, "predicted": PRED,
           "priming": json.load(open(os.path.join(R, "a3c_priming_info.json"))),
           "gate": json.load(open(os.path.join(R, "a3c_gate.json")))["summary"]}
    for name in ("Hp", "Hl"):
        rs = load(name)
        if len(rs) == 16:
            s = summ(name, rs)
            out[name] = s
            out[name]["verdicts"] = verdicts(s, name)
        else:
            out[name] = {"n": len(rs), "incomplete": True}
    for src in ("a3P",):
        for name in ("Hp", "Hl"):
            p = os.path.join(R, f"a3c_replay_{src}_{name}.json")
            if os.path.exists(p):
                out[f"replay_{src}_{name}"] = json.load(open(p))["summary"]
    if len(load("Hl")) == 16:
        out["local_model"] = local_calls()
        cpu = os.path.join(R, "a3c_local_cpu.json")
        if os.path.exists(cpu):
            out["local_model"]["process"] = json.load(open(cpu))
    path, digest = save("a3c_prose", out)
    print(json.dumps({k: (v if not isinstance(v, dict) or "verdicts" not in v else
                          {kk: v[kk] for kk in ("channel_tok", "channel_bpe", "exact", "replica", "heal0",
                                                "trunc_silent", "instr_bpc", "verdicts")})
                      for k, v in out.items() if k not in ("reuse",)}, indent=1, default=str))
    print(path, digest)


if __name__ == "__main__":
    main()
