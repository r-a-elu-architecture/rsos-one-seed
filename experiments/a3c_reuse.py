"""A3c re-use check (PREREGISTRATION_A3C.md): frozen files unchanged; A3's D and A3b's H-dragon replay byte for byte.

    python experiments/a3c_reuse.py      -> results/a3c_reuse.json
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import a1_agents as A                      # noqa: E402
import a3_run                              # noqa: E402
import a3b_hologram as H                   # noqa: E402

R = A.ROOT
FROZEN = ["experiments/a1_agents.py", "experiments/a3_run.py", "experiments/a3b_hologram.py",
          "experiments/a3b_hdragon.py"]
CHECK = ("success", "line_acc", "replica_success", "final_errors", "steps_failed", "n_calls", "channel_tok",
         "channel_bytes", "billed_tok", "out_tok")
DRIFT = ("key", "healed", "healed_zero_call")


def cmp(r, o, extra=()):
    bad = [k for k in CHECK + tuple(extra) if r[k] != o[k]]
    if [{k: e[k] for k in DRIFT} for e in r["drift"]] != [{k: e[k] for k in DRIFT} for e in o["drift"]]:
        bad.append("drift")
    return bad


def main():
    if H._BPE is None:
        sys.exit("tiktoken (o200k_base) required")
    diff = subprocess.run(["git", "-C", R, "diff", "9ef7933", "--"] + FROZEN, capture_output=True, text=True).stdout
    os.environ["A_TRANSCRIPTS"] = os.devnull
    rec = {(r["cond"], r["seed"]): r for r in json.load(open(os.path.join(R, "results", "a3_runs.json")))["runs"]}
    d_bad, nd = [], 0
    for line in open(os.path.join(R, "results", "a3_transcripts.jsonl")):
        t = json.loads(line)
        if t["cond"] != "D":
            continue
        nd += 1
        d_bad += [("D", t["seed"], k) for k in cmp(a3_run.replay(t), rec[("D", t["seed"])])]
    hrec = {json.loads(x)["seed"]: json.loads(x) for x in open(os.path.join(R, "results", "a3b_results_hd.jsonl"))}
    h_bad, nh, chan, bpe = [], 0, [], []
    for line in open(os.path.join(R, "results", "a3b_transcripts_hd.jsonl")):
        t = json.loads(line)
        r = H.replay_with(t, "Hd", t["seed"])
        nh += 1
        chan.append(r["channel_tok"]); bpe.append(r["channel_bpe"])
        h_bad += [("Hd", t["seed"], k) for k in cmp(r, hrec[t["seed"]], ("channel_bpe",))]
    out = {"frozen_diff_empty": diff == "", "D_replayed": nd, "D_mismatches": d_bad, "Hd_replayed": nh,
           "Hd_mismatches": h_bad, "Hd_chan_mean": sum(chan) / nh, "Hd_bpe_mean": sum(bpe) / nh,
           "pass": diff == "" and not d_bad and not h_bad and nd == 16 and nh == 16}
    json.dump(out, open(os.path.join(R, "results", "a3c_reuse.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
