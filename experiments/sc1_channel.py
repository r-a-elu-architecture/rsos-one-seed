"""SC1 channel measurement (0 model calls). PREREGISTRATION_SC1.md, section 5.

What one agent must transmit to keep the other robots' copies of the scene identical, per step, for every SC1 task,
with correct content in every encoding (the generator's ground truth), so the numbers measure the encodings, not a
model:

  G   full scene-graph sync: the scene after the step as a scene graph (nodes with attributes; edges on, owned_by,
      in_room), compact JSON. The common pattern when agents exchange world state.
  P   delta with values: RFC 6902 JSON Patch of the step (flat paths, the most compact form of a value delta), plus
      the 12-digit state digest so the receiver can check its copy (the same integrity layer as RSOS).
  R   RSOS program: the step as RSOS operations (key names and relations, no values the sender computed), plus the
      12-digit digest. The receiver's runtime computes the values.
  C   the same program in Core syntax (neutral names), plus the digest.

Also measured: the planner's input in the A7/A8 protocol for one-call JSON Patch (B2, full state shown) and RSOS
blind (X5b, requests only), captured from the harness with an oracle planner.

Units: UTF-8 bytes (bits = 8 x bytes) and the regex token count used by A1-A5 (`a1_agents.ntok`). BPE token counts
(o200k) are added by the owner's run, where tiktoken is installed; every compactness claim must also hold in BPE.

    python experiments/sc1_channel.py        # -> results/sc1_channel.json (with a sha256 of its numbers)
"""

import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))
import a1_agents as A                      # noqa: E402
import a5_run as R5                        # noqa: E402
import a7_arms as S                        # noqa: E402
import sc1_tasks as SC                     # noqa: E402
from rsoslang.core import compile_rsos, state_digest, to_core_text  # noqa: E402

try:
    import tiktoken
    _ENC = tiktoken.get_encoding("o200k_base")
except Exception:                          # noqa: BLE001
    _ENC = None

EDGE = {"on": "on", "owner": "owned_by", "room": "in_room"}


def scene_graph(state):
    nodes, edges = {}, []
    for k, v in state.items():
        o, f = k.split(".", 1)
        nodes.setdefault(o, {"id": o})
        if f in EDGE:
            edges.append({"s": o, "r": EDGE[f], "o": v})
        else:
            nodes[o][f] = int(v) if v.isdigit() else v
    return json.dumps({"nodes": list(nodes.values()), "edges": edges}, separators=(",", ":"))


def json_patch(a, b):
    out = [{"op": "remove", "path": "/" + x} for x in a if x not in b]
    out += [{"op": "replace" if x in a else "add", "path": "/" + x, "value": b[x]} for x in b if a.get(x) != b[x]]
    return json.dumps(out, separators=(",", ":"))


def size(s):
    r = {"bytes": len(s.encode()), "regex_tokens": A.ntok(s)}
    if _ENC is not None:
        r["o200k_tokens"] = len(_ENC.encode(s))
    return r


def add(acc, key, s):
    m = size(s)
    for u, v in m.items():
        acc.setdefault(key, {}).setdefault(u, 0)
        acc[key][u] += v


def planner_inputs(seed):
    """The prompt each arm's planner receives (system excluded), captured with an oracle planner; 0 model calls."""
    out = {}
    task = A.make_task(seed)
    for arm in ("B2", "X5b"):
        seen = {}

        def planner(prompt, ctx, task=task, arm=arm):
            seen.setdefault("prompt", prompt)
            body = []
            for line in prompt.split("\n"):
                m = re.match(r"^#(\d+) (.*)$", line)
                if m:
                    k = int(m.group(1)) - 1
                    body.append(f"#{k + 1}\n" + (json_patch(task["truths"][k], task["truths"][k + 1]) if arm == "B2"
                                                 else R5.oracle_ops(m.group(2))))
            return "\n".join(body)

        def auditor(prompt, ctx):
            return "\n".join(f"{m} ok" for m in re.findall(r"^#(\d+) ", prompt, re.M))

        S.run_plan(arm, "SC1", seed, planner=planner, auditor=auditor)
        out[arm] = size(seen["prompt"])
    return out


def main():
    SC.patch("SC1")
    os.environ["A7_TRANSCRIPTS"] = os.devnull
    per_task, total, by_kind = [], {}, {}
    for seed in SC.SEEDS["SC1"]:
        t = A.make_task(seed)
        acc = {}
        for k, req in enumerate(t["requests"]):
            a, b = t["truths"][k], t["truths"][k + 1]
            dig = state_digest(b)
            rsos = R5.oracle_ops(req)
            core = to_core_text(compile_rsos(rsos))
            msgs = {"G_full_scene_graph": scene_graph(b), "P_json_patch_plus_digest": json_patch(a, b) + "\n" + dig,
                    "R_rsos_plus_digest": rsos + "\n" + dig, "C_core_plus_digest": core + "\n" + dig}
            kind = rsos.split()[0]
            for name, s in msgs.items():
                add(acc, name, s)
                add(by_kind.setdefault(kind, {}), name, s)
        add(acc, "digest_only_replica_check", state_digest(t["final"]))
        add(acc, "full_state_replica_check", scene_graph(t["final"]))
        row = {"seed": seed, "steps": len(t["requests"]), "keys_init": len(t["init"]), "channel": acc,
               "planner_input": planner_inputs(seed)}
        per_task.append(row)
        for name, m in acc.items():
            for u, v in m.items():
                total.setdefault(name, {}).setdefault(u, 0)
                total[name][u] += v
        for arm, m in row["planner_input"].items():
            for u, v in m.items():
                total.setdefault(f"planner_input_{arm}", {}).setdefault(u, 0)
                total[f"planner_input_{arm}"][u] += v

    def ratio(x, y, u):
        return round(total[x][u] / total[y][u], 4)
    units = ["bytes", "regex_tokens"] + (["o200k_tokens"] if _ENC else [])
    ratios = {u: {"R_vs_P": ratio("R_rsos_plus_digest", "P_json_patch_plus_digest", u),
                  "R_vs_G": ratio("R_rsos_plus_digest", "G_full_scene_graph", u),
                  "C_vs_P": ratio("C_core_plus_digest", "P_json_patch_plus_digest", u),
                  "X5b_vs_B2_planner_input": ratio("planner_input_X5b", "planner_input_B2", u),
                  "digest_vs_full_replica_check": ratio("digest_only_replica_check", "full_state_replica_check", u)}
              for u in units}
    kinds = {k: {"steps": None, **{n: m for n, m in v.items()}} for k, v in by_kind.items()}
    for k in kinds:
        kinds[k]["steps"] = sum(1 for x in SC.SEEDS["SC1"] for r in A.make_task(x)["requests"]
                                if R5.oracle_ops(r).split()[0] == k)
        kinds[k]["R_vs_P_bytes"] = round(by_kind[k]["R_rsos_plus_digest"]["bytes"]
                                         / by_kind[k]["P_json_patch_plus_digest"]["bytes"], 4)
    out = {"set": "SC1", "tasks": len(per_task), "units": units, "total": total, "ratios": ratios,
           "by_operation": kinds, "per_task": per_task}
    out["sha256"] = hashlib.sha256(json.dumps({k: out[k] for k in ("total", "ratios", "by_operation")},
                                              sort_keys=True).encode()).hexdigest()
    p = os.path.join(ROOT, "results", "sc1_channel.json")
    json.dump(out, open(p, "w"), indent=1)
    print(json.dumps({"ratios": ratios, "R_vs_P_bytes_by_operation": {k: v["R_vs_P_bytes"] for k, v in kinds.items()},
                      "steps_by_operation": {k: v["steps"] for k, v in kinds.items()},
                      "sha256": out["sha256"]}, indent=1))


if __name__ == "__main__":
    main()
