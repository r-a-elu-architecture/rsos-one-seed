"""A3c: the design's gate before the live run (dev seeds only): build H-pred on 31 priming runs, measure the 32nd,
all 32 ways. -> results/a3c_gate.json"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import a3c_hpred as P                      # noqa: E402
import a3c_run as RUN                      # noqa: E402
from a3c_edges import EDGE                 # noqa: E402,F401

os.environ["A_TRANSCRIPTS"] = os.devnull
recs = {json.loads(x)["seed"]: json.loads(x) for x in open(os.path.join(RUN.R, "a3c_priming_transcripts.jsonl"))}
out = []
for j in RUN.PRIME_SEEDS:
    c = P.HPred(); c.persist = True; c.M = P.Model()
    for s in RUN.PRIME_SEEDS:
        if s != j:
            RUN.replay(recs[s], c, s, "gate_build")
    c.M.halve_all()
    t = RUN.codec_of("Hp", primed=False); t.primed = c.M
    r = RUN.attach(RUN.replay(recs[j], t, j, "gate"), t)
    out.append({"seed": j, "chan": r["channel_tok"], "bpe": r["channel_bpe"], "success": r["success"],
                "instr_bits": r["codec_stats"]["instr_bits"], "instr_chars": r["codec_stats"]["instr_chars"],
                "n_instr": r["codec_stats"]["n_instr"]})
n = len(out)
bits = sum(o["instr_bits"] for o in out); chars = sum(o["instr_chars"] for o in out)
ni = sum(o["n_instr"] for o in out) / n
bpc = bits / chars
honest = 71 + 14 * ((bits / sum(o["n_instr"] for o in out)) / 15.53 + 0.5) + 7      # design's formula
summ = {"folds": n, "chan_mean": sum(o["chan"] for o in out) / n, "bpe_mean": sum(o["bpe"] for o in out) / n,
        "heldout_instr_bpc": bpc, "instr_per_task": ni, "design_threshold_bpc": 0.72,
        "design_honest_prediction_if_above": honest}
json.dump({"summary": summ, "folds": out}, open(os.path.join(RUN.R, "a3c_gate.json"), "w"), indent=1)
print(json.dumps(summ, indent=1))
